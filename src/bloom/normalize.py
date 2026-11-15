"""Raw -> canonical tables (observations, forecasts). Pure, reproducible transforms."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

from .labels import label_observed_window, summarize_histogram


def cyan_weekly_to_observations(paths: list[Path], lake_id: str, min_valid: int) -> pd.DataFrame:
    rows = []
    for p in paths:
        d = json.loads(Path(p).read_text())
        if d.get("daily") is not False:
            raise ValueError(f"{p}: expected weekly composites (daily=false)")
        for key, counts in d["data"].items():
            y, doy = (int(x) for x in key.split())
            start = dt.date(y, 1, 1) + dt.timedelta(days=doy - 1)
            s = summarize_histogram(counts)
            rows.append(dict(lake_id=lake_id, start=pd.Timestamp(start),
                             end=pd.Timestamp(start + dt.timedelta(days=6)),
                             **s, label_state=label_observed_window(s["median_dn"], s["n_valid"], min_valid),
                             metric="cyan_weekly_dn_hist", product_version="unreported_by_api",
                             source_ref=Path(p).name))
    df = pd.DataFrame(rows).sort_values("start").reset_index(drop=True)
    if df.duplicated(["lake_id", "start"]).any():
        raise ValueError("duplicate lake-week observations")
    if not (df["start"].dt.day_of_week == 6).all():  # Sunday
        bad = df.loc[df["start"].dt.day_of_week != 6, "start"].tolist()
        raise ValueError(f"CyAN weeks not starting on Sunday: {bad[:5]}")
    return df


def epa_forecasts(csv_path: Path, comid: int, lake_id: str) -> pd.DataFrame:
    f = pd.read_csv(csv_path)
    f = f[f["COMID"] == comid].copy()
    start = pd.to_datetime(f["Date"].str.split(" to ").str[0], format="%b-%d-%Y")
    end = pd.to_datetime(f["WeekEndDate"], format="%m/%d/%Y")
    if not ((end - start).dt.days == 6).all():
        raise ValueError("forecast windows are not 7 days")
    p = f["Percent_chance_of_cyanoHAB"].astype(float) / 100.0
    if ((p < 0) | (p > 1)).any() or p.isna().any():
        raise ValueError("invalid forecast probability")
    out = pd.DataFrame(dict(lake_id=lake_id, valid_start=start, valid_end=end, p_bloom=p,
                            model_id="EPA_INLA_CONUS_operational",
                            issued_at=pd.NaT, available_at=pd.NaT,  # not in archive
                            retrospective_flag="unknown_issue_time",
                            source_ref=Path(csv_path).name))
    if out.duplicated(["lake_id", "valid_start"]).any():
        raise ValueError("duplicate forecast lake-weeks")
    return out.sort_values("valid_start").reset_index(drop=True)
