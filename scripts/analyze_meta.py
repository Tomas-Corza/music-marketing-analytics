"""Summarize Meta Insights campaign CSVs without exposing user-level data."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import pandas as pd


def action_count(value, action_type='landing_page_view'):
    """Extract an action count from Meta's JSON/Python-style actions arrays."""
    if pd.isna(value) if not isinstance(value, (list, dict)) else False:
        return 0.0
    if isinstance(value, str):
        import ast
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                return 0.0
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return 0.0
    return sum(float(item.get('value', 0)) for item in value if isinstance(item, dict) and item.get('action_type') == action_type)


def summarize(frame, group_columns):
    df = frame.copy()
    for col in ('spend', 'impressions', 'clicks', 'inline_link_clicks'):
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0) if col in df else 0.0
    df['landing_page_views'] = df['actions'].map(action_count) if 'actions' in df else 0.0
    columns = ['spend', 'impressions', 'clicks', 'inline_link_clicks', 'landing_page_views']
    result = df.groupby(group_columns, dropna=False)[columns].sum().reset_index() if group_columns else pd.DataFrame([df[columns].sum()])
    result['cost_per_lpv'] = result['spend'].div(result['landing_page_views'].replace(0, float('nan')))
    result['link_ctr_pct'] = result['inline_link_clicks'].div(result['impressions'].replace(0, float('nan'))).mul(100)
    return result.sort_values('spend', ascending=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', default='data/campaigns_overall.csv')
    parser.add_argument('--group-by', default='campaign_name', help='Comma-separated group fields')
    parser.add_argument('--output', default='outputs/campaign_summary.csv')
    args = parser.parse_args()
    source = Path(args.input)
    if not source.exists():
        parser.error(f'Input missing: {source}. Export CSVs first or supply --input.')
    frame = pd.read_csv(source)
    groups = [s.strip() for s in args.group_by.split(',') if s.strip()]
    missing = [s for s in groups if s not in frame.columns]
    if missing:
        parser.error(f'Missing group columns: {missing}. Available: {list(frame.columns)}')
    summary = summarize(frame, groups)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out, index=False)
    print(summary.to_string(index=False))
    print(f'\nSaved: {out}')


if __name__ == '__main__':
    main()
