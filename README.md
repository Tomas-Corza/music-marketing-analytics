# Music Marketing Analytics

**Python tools for Meta Ads reporting and music-marketing campaign analysis**  
Prepared by Tomas Corza

This repository documents a repeatable workflow for exporting, validating, and analyzing Meta Ads campaign data used in independent music marketing. It includes reusable code, setup instructions, and basic tests—not private client data.

## What the scripts do

| Script | Purpose |
|---|---|
| `scripts/export_meta.py` | Download 10 Meta Insights report types: campaign, ad set and ad performance, geography, demographics, platform, placement, and monthly trends. |
| `scripts/validate_exports.py` | Inventory CSV exports and report row/column counts or unreadable files. |
| `scripts/analyze_meta.py` | Aggregate spend, impressions, link clicks and landing-page views; calculate cost per landing-page view and link CTR. |

> **Source-history note:** This repository contains a cleaned, reproducible implementation of Meta export and campaign-analysis workflows. It is not a byte-for-byte archive of every original script. Review any additional locally saved scripts before describing the repository as a complete collection.

## Quick start (macOS / Linux)

```bash
cd music-marketing-analytics
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with a Meta Marketing API access token and ad account ID. **Never commit `.env`, tokens, or raw exports.** Meta Insights permissions and API field/breakdown support depend on account access and API version.

Export a historical period:

```bash
python scripts/export_meta.py --start 2023-10-06 --end 2026-11-05
```

Check existing exports and generate a campaign summary:

```bash
python scripts/validate_exports.py --directory data
python scripts/analyze_meta.py --input data/campaigns_overall.csv
python scripts/analyze_meta.py --input data/campaigns_country.csv --group-by country --output outputs/by_country.csv
python scripts/analyze_meta.py --input data/ads_placement.csv --group-by publisher_platform,platform_position --output outputs/by_placement.csv
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Metric definitions

- **Landing-page views (LPVs):** Reported Meta `landing_page_view` actions, not Spotify streams or saves.
- **Cost per LPV:** Spend / LPVs, blank when LPVs = 0.
- **Link CTR:** Inline link clicks / impressions × 100.
- **Zero LPVs:** Check destination, event tracking, objectives, and attribution settings before assuming an ad generated no real visits.

## Privacy and reuse

Do not upload Meta tokens, unpublished client results, emails, audience lists, or personally identifying information. The `data/`, `outputs/`, and `exports/` directories are gitignored. If you publish case studies, use permissioned or anonymized figures. Campaign names may reveal unreleased projects; scrub them from example data.

## Limitations

Meta Insights permissions and metric availability change over time; not every breakdown is supported for every account. Some requests may need async Insights jobs for very large date ranges. This starter currently uses paginated synchronous Insights requests, retries the initial request, and does not implement async job polling. Data exported with different attribution windows and objectives should not be compared as if directly equivalent.

## Author

Tomas Corza — Growth Marketing & Analytics  
https://tomascorza.me
