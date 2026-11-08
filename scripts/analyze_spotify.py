"""Compare Meta ad spend with Spotify for Artists saves.

Observational metrics only: saves are NOT necessarily caused by ads.
Input CSVs:
  Meta: spend, plus optional grouping columns (country, date, track)
  Spotify: saves, listeners, plus matching grouping columns
  Optional baseline: expected_saves plus the same grouping columns

Example:
  python scripts/analyze_spotify.py --meta data/meta_spend.csv \
    --spotify data/spotify_saves.csv --group-by country \
    --output outputs/spotify_by_country.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

GROUPS = ("country", "date", "track")


def read_data(path: str, required: str, groups: list[str]) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={key: "string" for key in groups})
    missing = set(groups + [required]) - set(frame.columns)
    if missing:
        raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")
    frame[required] = pd.to_numeric(frame[required], errors="raise")
    if frame[required].isna().any() or (frame[required] < 0).any():
        raise ValueError(f"{path}: {required} must be nonnegative and not blank")
    for key in groups:
        if frame[key].isna().any() or frame[key].str.strip().eq("").any():
            raise ValueError(f"{path}: {key} contains empty group values")
        frame[key] = frame[key].str.strip()
    return frame


def aggregate(frame: pd.DataFrame, measure: str, groups: list[str]) -> pd.DataFrame:
    if groups:
        return frame.groupby(groups, dropna=False, as_index=False)[measure].sum()
    return pd.DataFrame({measure: [frame[measure].sum()]})


def calculate(meta: pd.DataFrame, spotify: pd.DataFrame,
              groups: list[str], baseline: pd.DataFrame | None = None) -> pd.DataFrame:
    """Aggregate by shared keys; never assume a campaign maps to a track."""
    spend = aggregate(meta, "spend", groups)
    saves = aggregate(spotify, "saves", groups)
    if "listeners" in spotify.columns:
        listeners = aggregate(spotify, "listeners", groups)
        saves = saves.merge(listeners, on=groups, how="outer", validate="one_to_one") if groups else saves.assign(listeners=listeners["listeners"])
    # An outer join reveals unmatched locations/dates rather than silently misattributing.
    out = spend.merge(saves, on=groups, how="outer", indicator=True, validate="one_to_one") if groups else pd.concat([spend, saves], axis=1)
    if groups and (out["_merge"] != "both").any():
        bad = out.loc[out["_merge"] != "both", groups + ["_merge"]]
        raise ValueError(f"Unmatched Meta/Spotify groups; fix inputs before comparison:\n{bad.to_string(index=False)}")
    out = out.drop(columns=["_merge"], errors="ignore")
    out["saves_per_dollar"] = out["saves"].div(out["spend"].where(out["spend"].gt(0)))
    out["cost_per_save"] = out["spend"].div(out["saves"].where(out["saves"].gt(0)))
    if "listeners" in out:
        out["save_rate_pct"] = 100 * out["saves"].div(out["listeners"].where(out["listeners"].gt(0)))
    if baseline is not None:
        expected = aggregate(baseline, "expected_saves", groups)
        if groups:
            out = out.merge(expected, on=groups, how="left", validate="one_to_one")
            if out["expected_saves"].isna().any():
                raise ValueError("Baseline is missing at least one Meta/Spotify group")
        else:
            out["expected_saves"] = expected["expected_saves"].iloc[0]
        out["estimated_incremental_saves"] = out["saves"] - out["expected_saves"]
        positive = out["estimated_incremental_saves"].where(out["estimated_incremental_saves"].gt(0))
        out["cost_per_estimated_incremental_save"] = out["spend"].div(positive)
    return out.sort_values("saves_per_dollar", ascending=False, na_position="last").reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--meta", required=True, help="Meta spend CSV with a 'spend' column")
    parser.add_argument("--spotify", required=True, help="Spotify CSV with 'saves', optional 'listeners'")
    parser.add_argument("--baseline", help="Optional modeled baseline CSV containing 'expected_saves'")
    parser.add_argument("--group-by", choices=GROUPS, nargs="*", default=[],
                        help="Common group keys in both CSVs, e.g. country date")
    parser.add_argument("--output", default="outputs/spotify_efficiency.csv")
    args = parser.parse_args()
    groups = args.group_by
    meta = read_data(args.meta, "spend", groups)
    spotify = read_data(args.spotify, "saves", groups)
    if "listeners" in spotify:
        spotify["listeners"] = pd.to_numeric(spotify["listeners"], errors="raise")
        if spotify["listeners"].isna().any() or spotify["listeners"].lt(0).any():
            parser.error("listeners must be nonnegative and not blank")
    baseline = read_data(args.baseline, "expected_saves", groups) if args.baseline else None
    result = calculate(meta, spotify, groups, baseline)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out, index=False)
    print(f"Saved {len(result)} rows to {out}")
    print("Note: saves per dollar is observational, not causal attribution.")


if __name__ == "__main__":
    main()
