"""Export Meta Ads Insights using asynchronous jobs, without storing credentials in code.

Example: python scripts/export_meta.py --start 2026-08-01 --end 2026-10-31
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')

# name: (report level, breakdowns, daily time increment)
REPORTS = {
    'campaigns_overall': ('campaign', None, None),
    'campaigns_country': ('campaign', 'country', None),
    'campaigns_monthly': ('campaign', None, 'monthly'),
    'adsets_overall': ('adset', None, None),
    'adsets_country': ('adset', 'country', None),
    'adsets_age_gender': ('adset', 'age,gender', None),
    'ads_overall': ('ad', None, None),
    'ads_platform': ('ad', 'publisher_platform', None),
    'ads_placement': ('ad', 'publisher_platform,platform_position', None),
    'ads_monthly': ('ad', None, 'monthly'),
}

BASE_FIELDS = [
    'campaign_id', 'campaign_name', 'spend', 'impressions', 'reach',
    'clicks', 'inline_link_clicks', 'actions', 'cost_per_action_type',
    'date_start', 'date_stop',
]
VIDEO_FIELDS = [
    'video_p25_watched_actions', 'video_p50_watched_actions',
    'video_p75_watched_actions', 'video_p95_watched_actions',
]


def report_fields(level: str, breakdown: str | None) -> str:
    fields = list(BASE_FIELDS)
    if level in ('adset', 'ad'):
        fields += ['adset_id', 'adset_name']
    if level == 'ad':
        fields += ['ad_id', 'ad_name']
        # Video metrics are collected on non-breakdown ad reports.
        if not breakdown:
            fields += VIDEO_FIELDS
    return ','.join(fields)


def api_request(session, method, url, *, retries=5, **kwargs):
    """Retry transient HTTP failures; don't retry invalid credentials/parameters."""
    for attempt in range(retries):
        try:
            response = session.request(method, url, timeout=90, **kwargs)
            response.raise_for_status()
            payload = response.json()
            if 'error' in payload:
                raise RuntimeError(str(payload['error']))
            return payload
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status not in (429, 500, 502, 503, 504) or attempt == retries - 1:
                raise
        except (requests.ConnectionError, requests.Timeout):
            if attempt == retries - 1:
                raise
        time.sleep(min(2 ** attempt, 16))
    raise RuntimeError('API request failed')


def fetch_report(session, base_url, account, start, end, level, breakdown=None,
                 increment=None, poll_seconds=5, max_polls=120):
    params = {
        'level': level,
        'fields': report_fields(level, breakdown),
        'time_range': json.dumps({'since': start, 'until': end}),
        'limit': 500,
    }
    if breakdown:
        params['breakdowns'] = breakdown
    if increment:
        params['time_increment'] = increment

    job = api_request(session, 'POST', f'{base_url}/{account}/insights', data=params)
    report_id = job['report_run_id']
    for _ in range(max_polls):
        status = api_request(session, 'GET', f'{base_url}/{report_id}')
        state = status.get('async_status')
        if state == 'Job Completed':
            break
        if state in ('Job Failed', 'Job Skipped'):
            raise RuntimeError(f'Report {report_id} failed: {status}')
        time.sleep(poll_seconds)
    else:
        raise TimeoutError(f'Report {report_id} did not finish')

    rows = []
    url = f'{base_url}/{report_id}/insights'
    params = {'limit': 500}
    while url:
        data = api_request(session, 'GET', url, params=params)
        rows.extend(data.get('data', []))
        url = data.get('paging', {}).get('next')
        params = None  # Next URLs already include pagination parameters.
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', required=True, help='YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='YYYY-MM-DD')
    parser.add_argument('--output', default='data', help='Local output directory (gitignored by default)')
    parser.add_argument('--report', choices=REPORTS, help='Run one report instead of all ten')
    args = parser.parse_args()
    try:
        start, end = date.fromisoformat(args.start), date.fromisoformat(args.end)
    except ValueError:
        parser.error('Dates must use YYYY-MM-DD')
    if end < start:
        parser.error('--end must be on or after --start')

    token = os.environ.get('META_ACCESS_TOKEN')
    account = os.environ.get('META_AD_ACCOUNT_ID', '').strip()
    version = os.environ.get('META_API_VERSION', 'v26.0')
    if not token or not account:
        parser.error('Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID in local .env')
    if not account.startswith('act_'):
        account = 'act_' + account

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    selected = {args.report: REPORTS[args.report]} if args.report else REPORTS
    with requests.Session() as session:
        session.headers.update({'Authorization': f'Bearer {token}'})
        for name, (level, breakdown, increment) in selected.items():
            print(f'Exporting {name}...', flush=True)
            rows = fetch_report(session, f'https://graph.facebook.com/{version}',
                                account, args.start, args.end, level, breakdown, increment)
            path = output / f'{name}.csv'
            pd.json_normalize(rows, sep='_').to_csv(path, index=False)
            print(f'  {len(rows)} rows saved to {path}', flush=True)


if __name__ == '__main__':
    main()
