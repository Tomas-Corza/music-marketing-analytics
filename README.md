# Music Marketing Analytics

**Meta Ads and Spotify engagement analysis tools**  
Prepared by Tomas Corza

A client-neutral Python toolkit to export Meta Ads reports, analyze advertising efficiency, compare observed Spotify saves to advertising spend, and explore country performance in an interactive dashboard. The built-in dashboard example contains fictional data only.

## Interactive dashboard

Launch locally:

```bash
git pull origin main
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run dashboard.py
```

Streamlit should open a local dashboard in your browser (normally http://localhost:8501).

In the sidebar you can:
- **Explore synthetic example:** see fictional advertising and Spotify statistics immediately.
- **Upload your CSVs:** choose a Meta country export and a Spotify country summary covering the same date period, plus an optional modeled baseline.
- Inspect overview metrics, compare countries, and download a country-level summary.

### CSV format

Meta CSV (example):
```csv
country,spend,actions,impressions,inline_link_clicks
United States,100,"[{""action_type"":""landing_page_view"",""value"":""80""}]",8000,100
Poland,50,"[{""action_type"":""landing_page_view"",""value"":""42""}]",4500,60
```

Spotify CSV (example):
```csv
country,saves,listeners
United States,55,400
Poland,31,250
```

Optionally include a separate modeled baseline CSV with `country,expected_saves`. Every country in the Meta CSV must also appear in Spotify (and vice versa); country spelling must match. Spotify file formats vary and may need column normalization. Only compare equivalent periods, countries, and definitions. A listeners total summed across days is not necessarily a unique listener count for the entire period.

**Interpretation:** Observed saves / ad spend is not proof the ads generated those saves. Organic and playlist discovery can contribute to Spotify saves. An optional modeled baseline is an estimate, not a causal result.

## Command-line scripts

| File | Purpose |
|---|---|
| `scripts/export_meta.py` | Export up to 10 predefined Meta Insights reports with async reporting and pagination |
| `scripts/validate_exports.py` | Inspect CSV exports for unreadable data and counts |
| `scripts/analyze_meta.py` | Summarize ad spend, clicks, landing-page views, and efficiency |
| `scripts/analyze_spotify.py` | Compare Spotify saves and listeners to ad spend by country, date, or track |
| `scripts/dashboard_data.py` | Validate and combine country-level Meta and Spotify data |
| `dashboard.py` | Streamlit dashboard with sample mode and CSV uploads |

See [SPOTIFY_ANALYSIS.md](SPOTIFY_ANALYSIS.md) for the Spotify calculation methodology.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The dashboard's synthetic example requires no Meta token. For live Meta reporting, create a local `.env` from `.env.example`, add your own authorized API credentials, and run `python scripts/export_meta.py --help`.

## Privacy

Do not publish tokens, client exports, unpublished campaign names, private Spotify data, audience lists, or personal information. The repository ignores `data/`, `outputs/`, and common CSV file types. Public hosting of a dashboard with real uploads may involve third-party processing; use only data you are authorized to upload.

## Limitations

The dashboard is a **local CSV analysis tool**, not a live Meta/Spotify API dashboard. Automated tests validate calculation logic, not live API connectivity. Meta attribution windows, field support, and exports may vary. This repository is a reproducible, client-neutral implementation; it does not claim to contain every line of the original local research scripts.

## Author

Tomas Corza — Growth Marketing & Analytics  
https://tomascorza.me
