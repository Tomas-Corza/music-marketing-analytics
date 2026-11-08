# Spotify saves-per-dollar analysis

Prepared by Tomas Corza

This optional module compares **observed** Spotify saves and listeners with Meta advertising spend. It does **not** prove that an ad caused a save. Spotify saves can come from playlists, organic discovery, other advertising, and many other sources.

## Prepare your CSVs

Export and prepare aggregate totals for the **same dates and geography**. Spotify for Artists export formats vary, so normalize field names before running the tool. These are synthetic illustrative values, not client data.

**meta_spend.csv**
```csv
country,spend
US,100
PL,50
```

**spotify_saves.csv**
```csv
country,saves,listeners
US,80,300
PL,60,200
```

Optional **baseline.csv**: modeled saves expected without the campaign. The quality of this estimate depends on your experimental design; do not treat it as a measured causal effect.
```csv
country,expected_saves
US,40
PL,45
```

```bash
python scripts/analyze_spotify.py --meta data/meta_spend.csv --spotify data/spotify_saves.csv --group-by country --output outputs/spotify_by_country.csv

# Optional modeled baseline
python scripts/analyze_spotify.py --meta data/meta_spend.csv --spotify data/spotify_saves.csv --baseline data/baseline.csv --group-by country
```

Without `--group-by`, the tool computes one total for each input. With `--group-by`, matching values must exist in both files. Allowed keys are `country`, `date`, and `track`. Use `track` only when you have a defensible way to assign spend to tracks in the Meta input.

## Metrics

| Output | Formula |
|---|---|
| saves_per_dollar | Spotify saves / Meta spend |
| cost_per_save | Meta spend / Spotify saves |
| save_rate_pct | 100 × Spotify saves / listeners |
| estimated_incremental_saves (optional) | Observed saves − modeled expected saves |
| cost_per_estimated_incremental_save (optional) | Meta spend / positive estimated incremental saves |

Zero denominators produce blank metrics. Negative estimated incremental saves remain negative, but the incremental cost metric is blank because a cost-per-gain is not meaningful.

**Important:** Daily Spotify saves and unique listeners can have different counting properties; summing listeners over days does not yield unique listeners for the entire period. Use consistent, appropriately aggregated measures. Do not describe observed saves-per-dollar as campaign-attributed return.
