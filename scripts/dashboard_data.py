"""Strict, client-neutral Meta + Spotify reporting for the Streamlit dashboard."""
from __future__ import annotations
import pandas as pd
from scripts.analyze_meta import summarize
from scripts.analyze_spotify import calculate


def _positive_numeric(df: pd.DataFrame, name: str, required: bool = True) -> pd.DataFrame:
    df = df.copy()
    if name not in df:
        if required:
            raise ValueError(f"Missing required column: {name}")
        return df
    df[name] = pd.to_numeric(df[name], errors="raise")
    if df[name].isna().any() or df[name].lt(0).any():
        raise ValueError(f"{name} must be nonnegative and contain no missing values")
    return df


def _country(df: pd.DataFrame, source: str) -> pd.DataFrame:
    if "country" not in df:
        raise ValueError(f"{source} needs a country column")
    out = df.copy()
    out["country"] = out["country"].astype("string").str.strip()
    if out["country"].isna().any() or out["country"].eq("").any():
        raise ValueError(f"{source} has blank country values")
    return out


def prepare_dashboard(meta: pd.DataFrame, spotify: pd.DataFrame,
                      baseline: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """One matched country table and one overall total; refuse mismatched countries."""
    meta = _positive_numeric(_country(meta, "Meta"), "spend")
    spotify = _positive_numeric(_country(spotify, "Spotify"), "saves")
    if "listeners" in spotify:
        spotify = _positive_numeric(spotify, "listeners")
    if baseline is not None:
        baseline = _positive_numeric(_country(baseline, "Baseline"), "expected_saves")
    meta_summary = summarize(meta, ["country"])
    spotify_summary = calculate(meta[["country", "spend"]], spotify, ["country"], baseline)
    # calculate checks every matched country; the separate join includes Meta-only LPV metrics.
    by_country = spotify_summary.merge(meta_summary.drop(columns=["spend"]), on="country", validate="one_to_one")
    if len(by_country) != len(spotify_summary):
        raise ValueError("Meta countries could not be matched to Spotify countries")
    # Overall cost/saves metrics must be calculated from totals, not averages of country ratios.
    totals = {k: by_country[k].sum() for k in ("spend", "saves", "landing_page_views", "impressions", "inline_link_clicks") if k in by_country}
    totals["saves_per_dollar"] = totals["saves"] / totals["spend"] if totals["spend"] else float("nan")
    totals["cost_per_save"] = totals["spend"] / totals["saves"] if totals["saves"] else float("nan")
    return pd.DataFrame([totals]), by_country.sort_values("saves_per_dollar", ascending=False).reset_index(drop=True)


def demo_inputs() -> tuple[pd.DataFrame, pd.DataFrame, None]:
    """Clearly fictional data; never derived from client reports."""
    meta = pd.DataFrame({
        "country": ["United States", "Poland", "Mexico", "Canada"],
        "spend": [240, 100, 80, 120],
        "impressions": [22000, 11000, 9000, 10000],
        "inline_link_clicks": [300, 170, 95, 120],
        "actions": [
            '[{"action_type":"landing_page_view","value":"240"}]',
            '[{"action_type":"landing_page_view","value":"130"}]',
            '[{"action_type":"landing_page_view","value":"70"}]',
            '[{"action_type":"landing_page_view","value":"105"}]',
        ],
    })
    spotify = pd.DataFrame({
        "country": ["United States", "Poland", "Mexico", "Canada"],
        "saves": [110, 96, 38, 52], "listeners": [650, 300, 260, 380],
    })
    return meta, spotify, None
