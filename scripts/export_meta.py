"""Export Meta Ads Insights at campaign, ad set, and ad level.

Run from the project root:
    python scripts/export_meta.py --start 2023-10-06 --end 2026-11-05

Credentials are read from environment variables or a local .env file.
This is a reproducible implementation of the export workflow; it is not a
byte-for-byte copy of a previously created local script.
"""
from __future__ import annotations
import argparse
import os
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parents[1]
load_dotenv(BASE / '.env')

REPORTS = {
    'campaigns_overall': ('campaign', None, None),
    'campaigns_country': ('campaign', 'country', None),
    'campaigns_monthly': ('campaign', None, 1),
    'adsets_overall': ('adset', None, None),
    'adsets_country': ('adset', 'country', None),
    'adsets_age_gender': ('adset', 'age,gender', None),
    'ads_overall': ('ad', None, None),
    'ads_platform': ('ad', 'publisher_platform', None),
    'ads_placement': ('ad', 'publisher_platform,platform_position', None),
    'ads_monthly': ('ad', None, 1),
}

FIELDS = {
    'campaign': 'campaign_id,campaign_name,spend,impressions,reach,clicks,inline_link_clicks,actions,cost_per_action_type',
    'adset': 'campaign_id,campaign_name,adset_id,adset_name,spend,impressions,reach,clicks,inline_link_clicks,actions,cost_per_action_type',
    'ad': 'campaign_id,campaign_name,adset_id,adset_name,ad_id,ad_name,spend,impressions,reach,clicks,inline_link_clicks,actions,cost_per_action_type',
}


def fetch_report(session, account_id, token, version, start, end, level, breakdown, time_increment):
    url = f'https://graph.facebook.com/{version}/{account_id}/insights'
    params = {
        'access_token': token, 'level': level, 'fields': FIELDS[level],
        'time_range': {'since': start, 'until': end}, 'limit': 500,
    }
    # requests handles JSON encoding for form-style query params when given a string
    import json
    params['time_range'] = json.dumps(params['time_range'])
    if breakdown:
        params['breakdowns'] = breakdown
    if time_increment:
        params['time_increment'] = time_increment
    records = []
    for attempt in range(5):
        try:
            response = session.get(url, params=params, timeout=90)
            response.raise_for_status()
            payload = response.json()
            if 'error' in payload:
                raise RuntimeError(str(payload['error']))
            break
        except (requests.RequestException, RuntimeError):
            if attempt == 4:
                raise
            time.sleep(min(2 ** attempt, 16))
    while True:
        records.extend(payload.get('data', []))
        next_url = payload.get('paging', {}).get('next')
        if not next_url:
            return records
        response = session.get(next_url, timeout=90)
        response.raise_for_status()
        payload = response.json()
        if 'error' in payload:
            raise RuntimeError(str(payload['error']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', required=True, help='YYYY-MM-DD')
    parser.add_argument('--end', required=True, help='YYYY-MM-DD')
    parser.add_argument('--output', default='data')
    args = parser.parse_args()
    token = os.environ.get('META_ACCESS_TOKEN')
    account = os.environ.get('META_AD_ACCOUNT_ID', '')
    version = os.environ.get('META_API_VERSION', 'v22.0')
    if not token or not account:
        parser.error('Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID in .env')
    if not account.startswith('act_'):
        account = 'act_' + account
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    with requests.Session() as session:
        for name, (level, breakdown, increment) in REPORTS.items():
            print(f'Exporting {name}...', flush=True)
            rows = fetch_report(session, account, token, version, args.start, args.end, level, breakdown, increment)
            frame = pd.json_normalize(rows, sep='_')
            path = out / (name + '.csv')
            frame.to_csv(path, index=False)
            print(f'  {len(frame)} rows -> {path}', flush=True)


if __name__ == '__main__':
    main()
