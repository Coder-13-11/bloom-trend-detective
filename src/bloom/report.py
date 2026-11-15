"""Data inventory + Lake Okeechobee evidence figure + scenario table.
Usage: python -m bloom.report --out outputs/report
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from .normalize import cyan_weekly_to_observations, epa_forecasts
from . import scenario

OKEE_OID, OKEE_COMID = 6624886, 166757656


def inventory(raw="data/raw/D03_cyan") -> pd.DataFrame:
    rows = []
    for p in sorted(Path(raw).glob("cyan_weekly_*.json")):
        _, _, oid, yr = p.stem.split("_")
        n = len(json.loads(p.read_text())["data"])
        rows.append(dict(cyan_objectid=int(oid), year=int(yr), weeks=n))
    return pd.DataFrame(rows)


def okeechobee(out: Path):
    obs = cyan_weekly_to_observations(sorted(Path("data/raw/D03_cyan").glob(f"cyan_weekly_{OKEE_OID}_*.json")), "okeechobee", 1000)
    fc = epa_forecasts(Path("data/raw/D01_forecasts/AllWeeks_CyanForecasts.csv"), OKEE_COMID, "okeechobee")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        subplot_titles=("CyAN weekly composite, Lake Okeechobee (real data)",
                                        "EPA weekly forecast probability (archived, 2025–26)"))
    fig.add_trace(go.Scatter(x=obs.start, y=obs.frac_ge_bloom, name="fraction of valid pixels ≥ DN130 (~12 µg/L)", mode="lines"), 1, 1)
    fig.add_trace(go.Scatter(x=obs.start, y=obs.median_dn / 253, name="lake median DN / 253", mode="lines"), 1, 1)
    b = obs[obs.label_state == "bloom"]
    fig.add_trace(go.Scatter(x=b.start, y=[1.02] * len(b), mode="markers", name="EPA-rule bloom week (median ≥ 130)"), 1, 1)
    fig.add_hline(y=130 / 253, line_dash="dot", row=1, col=1)
    fig.add_trace(go.Scatter(x=fc.valid_start, y=fc.p_bloom, mode="lines+markers", name="EPA p(bloom)"), 2, 1)
    fig.update_layout(height=650, title="Lake Okeechobee — evidence view (data: EPA CyAN API; EPA forecast dashboard export)")
    fig.write_html(out / "okeechobee_evidence.html", include_plotlyjs="cdn")
    obs.assign(data_mode="REAL").to_csv(out / "okeechobee_weekly_observations.csv", index=False)
    yr = obs.assign(y=obs.start.dt.year).groupby("y").agg(
        weeks=("start", "size"), bloom_weeks=("label_state", lambda s: (s == "bloom").sum()),
        unknown=("label_state", lambda s: (s == "unknown").sum()),
        weeks_frac_ge_0_25=("frac_ge_bloom", lambda s: (s >= 0.25).sum()), max_frac=("frac_ge_bloom", "max"))
    return yr


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="outputs/report")
    out = Path(ap.parse_args(argv).out); out.mkdir(parents=True, exist_ok=True)
    inv = inventory(); inv.to_csv(out / "cyan_inventory.csv", index=False)
    print(f"CyAN files: {len(inv)}, lakes: {inv.cyan_objectid.nunique()}, years: {sorted(inv.year.unique())}, "
          f"empty lake-years: {(inv.weeks == 0).sum()}")
    yr = okeechobee(out); yr.to_csv(out / "okeechobee_by_year.csv"); print(yr.to_string())
    print(scenario.run(out=str(out)).drop(columns="data_mode").round(3).to_string())


if __name__ == "__main__":
    main()
