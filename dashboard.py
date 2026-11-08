"""Music marketing performance dashboard — Streamlit entry point."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from scripts.dashboard_data import prepare_dashboard, demo_inputs

st.set_page_config(page_title="Music Marketing Analytics", page_icon="🎵", layout="wide")
st.title("Music Marketing Analytics")
st.caption("Meta advertising + Spotify engagement | Prepared by Tomas Corza")
st.info("Spotify saves are observed engagement, not saves caused by advertising. Matching dates and countries is essential.")

with st.sidebar:
    st.header("Data source")
    mode = st.radio("Choose data", ["Explore synthetic example", "Upload your CSVs"], index=0)
    if mode == "Upload your CSVs":
        st.markdown("Upload CSVs with **country, spend, actions** (Meta) and **country, saves, listeners** (Spotify).")
        meta_file = st.file_uploader("Meta Ads CSV", type="csv", key="meta")
        spotify_file = st.file_uploader("Spotify CSV", type="csv", key="spotify")
        baseline_file = st.file_uploader("Optional modeled baseline CSV (country, expected_saves)", type="csv", key="baseline")
    else:
        st.caption("The sample uses fictional numbers and is not actual artist or campaign data.")

if mode == "Explore synthetic example":
    meta, spotify, baseline = demo_inputs()
else:
    if not (meta_file and spotify_file):
        st.warning("Upload both Meta and Spotify CSVs to view the dashboard, or select the example.")
        st.stop()
    try:
        meta = pd.read_csv(meta_file)
        spotify = pd.read_csv(spotify_file)
        baseline = pd.read_csv(baseline_file) if baseline_file else None
    except Exception as exc:
        st.error(f"Could not read CSV: {exc}")
        st.stop()

try:
    summary, by_country = prepare_dashboard(meta, spotify, baseline)
except (ValueError, KeyError, TypeError) as exc:
    st.error(f"Data validation error: {exc}")
    st.stop()

row = summary.iloc[0]
a, b, c, d, e = st.columns(5)
a.metric("Meta spend", f"${row['spend']:,.2f}")
b.metric("Meta landing-page views", f"{row['landing_page_views']:,.0f}")
c.metric("Spotify saves", f"{row['saves']:,.0f}")
d.metric("Observed saves per $1", f"{row['saves_per_dollar']:,.2f}" if pd.notna(row['saves_per_dollar']) else "N/A")
e.metric("Observed cost per save", f"${row['cost_per_save']:,.2f}" if pd.notna(row['cost_per_save']) else "N/A")

st.subheader("Country comparison")
metric = st.selectbox("Compare countries by", ["saves_per_dollar", "cost_per_save", "landing_page_views", "spend", "saves"],
    format_func=lambda x: {"saves_per_dollar": "Observed saves per $1", "cost_per_save": "Observed cost per save ($)", "landing_page_views": "Meta landing-page views", "spend": "Meta spend ($)", "saves": "Spotify saves"}[x])
st.bar_chart(by_country.set_index("country")[[metric]])
st.dataframe(by_country, hide_index=True, use_container_width=True)

if baseline is not None:
    st.caption("Modeled baseline columns are estimates, not experimentally verified causal lift.")
st.caption("Landing-page views come from Meta's landing_page_view action. Spotify saves and listeners are reported separately. Save rates are only meaningful when listener counts match the reporting period and aggregation.")
st.download_button("Download country results (CSV)", by_country.to_csv(index=False).encode("utf-8"),
                   file_name="music_marketing_country_summary.csv", mime="text/csv")

with st.expander("How to prepare your files"):
    st.markdown("""
    - Meta: export a **country breakdown** from Meta Insights with the columns `country`, `spend`, and `actions` (the JSON actions array containing `landing_page_view`). Optional: `impressions`, `inline_link_clicks`.
    - Spotify: prepare aggregated `country`, `saves`, and optionally `listeners` for the **same reporting dates**.
    - Optional baseline: `country`, `expected_saves`, from an explicitly documented model or experiment.
    - Country labels must match exactly. No matching at song or user level is inferred.
    - Never upload private client data to a publicly hosted dashboard without authorization. Local Streamlit runs keep uploaded files on your own machine.
    """)
