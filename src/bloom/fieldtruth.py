"""Protocol Amendment 4.
E2: has the satellite-field relationship drifted (same-week matchups, 2020-2025)?
E3: which signal better predicts what a field crew finds (2025-26 forecast windows)?
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from .backtest import load_observations
from .insitu import SEASON, load_results

SEED = 20261115
N_BOOT = 2000


def field_weeks(res: pd.DataFrame, match: pd.DataFrame) -> pd.DataFrame:
    d = res.merge(match[["station", "cyan_objectid"]], on="station")
    day = d.groupby(["cyan_objectid", "date"])["chl"].mean().reset_index()
    day["start"] = day["date"] - pd.to_timedelta((day["date"].dt.day_of_week + 1) % 7, unit="D")
    w = day.groupby(["cyan_objectid", "start"]).agg(field_chl=("chl", "mean"), n_field_dates=("chl", "size")).reset_index()
    w["log_chl"] = np.log10(w["field_chl"])
    return w


# ---------------- E2 ----------------
def _within(df: pd.DataFrame, cols: list[str], key: str) -> np.ndarray:
    return (df[cols] - df.groupby(key)[cols].transform("mean")).to_numpy(float)


def _fit(m: pd.DataFrame, y: str, xcols: list[str]) -> np.ndarray:
    A = _within(m, xcols, "cyan_objectid")
    b = _within(m, [y], "cyan_objectid")[:, 0]
    return np.linalg.lstsq(A, b, rcond=None)[0]


def _cluster_boot(m: pd.DataFrame, fn, n_boot=N_BOOT, seed=SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    groups = [g for _, g in m.groupby("cyan_objectid")]
    out = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(groups), len(groups))
        parts = [groups[i].assign(cyan_objectid=k) for k, i in enumerate(pick)]
        try:
            out.append(fn(pd.concat(parts, ignore_index=True)))
        except Exception:  # noqa: BLE001 - degenerate resample
            continue
    return np.array(out, float)


def drift(m: pd.DataFrame, y: str = "extent") -> dict:
    m = m.copy()
    months = sorted(m["month"].unique())[1:]
    for k in months:
        m[f"m{k}"] = (m["month"] == k).astype(float)
    years = sorted(m["year"].unique())
    for k in years[1:]:
        m[f"y{k}"] = (m["year"] == k).astype(float)
    mcols = [f"m{k}" for k in months]
    lin = ["log_chl", *mcols, "year_c"]
    m["year_c"] = m["year"] - years[0]
    fe = ["log_chl", *mcols, *[f"y{k}" for k in years[1:]]]
    b_lin = _fit(m, y, lin)
    bl = _cluster_boot(m, lambda d: _fit(d, y, lin)[[0, -1]])
    b_fe = _fit(m, y, fe)
    bf = _cluster_boot(m, lambda d: _fit(d, y, fe)[-(len(years) - 1):])
    ci = lambda a: (float(np.nanpercentile(a, 2.5)), float(np.nanpercentile(a, 97.5)))  # noqa: E731
    year_fx = [dict(year=int(years[0]), effect=0.0, lo=0.0, hi=0.0)]
    for i, k in enumerate(years[1:]):
        lo, hi = ci(bf[:, i])
        year_fx.append(dict(year=int(k), effect=float(b_fe[len(fe) - len(years) + 1 + i]), lo=lo, hi=hi))
    s_lo, s_hi = ci(bl[:, 1])
    c_lo, c_hi = ci(bl[:, 0])
    return dict(outcome=y, n_matchups=int(len(m)), lakes=int(m["cyan_objectid"].nunique()),
                per_year=m.groupby("year").size().to_dict(),
                year_slope=dict(est=float(b_lin[-1]), lo=s_lo, hi=s_hi),
                log_chl_coef=dict(est=float(b_lin[0]), lo=c_lo, hi=c_hi), year_effects=year_fx,
                verdict=("The satellite reads higher for the same field chlorophyll in later years" if s_lo > 0 else
                         "The satellite reads lower for the same field chlorophyll in later years" if s_hi < 0 else
                         "No drift shown"))


# ---------------- E3 ----------------
def _auc_pair(d: pd.DataFrame, a: str, b: str, ycol: str) -> float:
    y = d[ycol].to_numpy(int)
    if y.min() == y.max():
        raise ValueError("one class")
    return roc_auc_score(y, d[a]) - roc_auc_score(y, d[b])


def field_truth(ev: pd.DataFrame, fw: pd.DataFrame, thr: float) -> dict:
    j = ev.merge(fw.rename(columns={"start": "valid_start"}), on=["cyan_objectid", "valid_start"])
    j["y_field"] = (j["field_chl"] >= thr).astype(int)
    j["same_week_sat"] = j["label_state"].eq("bloom").astype(float)
    n, ev1 = len(j), int(j["y_field"].sum())
    out = dict(threshold_ugL=thr, windows=n, lakes=int(j["cyan_objectid"].nunique()), field_events=ev1,
               base_rate=float(j["y_field"].mean()) if n else None, by_year=j["valid_start"].dt.year.value_counts().to_dict())
    if n < 150 or ev1 < 30 or (n - ev1) < 30:
        out["verdict"] = "Inconclusive (too few windows or events)"
        return dict(summary=out, windows=j)
    sig = {"EPA forecast": "p_epa", "Last week's satellite extent": "lag1_frac", "Last week's satellite bloom state": "lag1_bloom",
           "Same-week satellite bloom state (reference, not a forecast)": "same_week_sat"}
    rows = []
    for name, col in sig.items():
        rows.append(dict(signal=name, n=n, roc_auc=float(roc_auc_score(j["y_field"], j[col])),
                         pr_auc=float(average_precision_score(j["y_field"], j[col]))))
    for name, col in {"Seasonal average (climatology)": "p_clim", "Logistic on last week's satellite state": "p_logit"}.items():
        s = j.dropna(subset=[col]) if col in j else j.iloc[0:0]
        if len(s) >= 150 and s["y_field"].nunique() == 2:
            rows.append(dict(signal=name + " [secondary]", n=int(len(s)), roc_auc=float(roc_auc_score(s["y_field"], s[col])),
                             pr_auc=float(average_precision_score(s["y_field"], s[col]))))
    out["metrics"] = rows
    est = _auc_pair(j, "p_epa", "lag1_frac", "y_field")
    b = _cluster_boot(j, lambda d: _auc_pair(d, "p_epa", "lag1_frac", "y_field"))
    lo, hi = float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))
    out["primary_auc_diff_epa_minus_lastweek"] = dict(est=float(est), lo=lo, hi=hi, n_boot=int(len(b)))
    if "p_logit" in j and j["p_logit"].notna().sum() >= 150:
        s = j.dropna(subset=["p_logit"])
        e2 = _auc_pair(s, "p_logit", "p_epa", "y_field")
        b2 = _cluster_boot(s, lambda d: _auc_pair(d, "p_logit", "p_epa", "y_field"))
        out["secondary_auc_diff_logistic_minus_epa"] = dict(est=float(e2), lo=float(np.percentile(b2, 2.5)), hi=float(np.percentile(b2, 97.5)))
    out["verdict"] = ("The forecast ranks field outcomes better than last week's satellite view" if lo > 0 else
                      "Last week's satellite view ranks field outcomes better than the forecast" if hi < 0 else
                      "No difference shown between the forecast and last week's satellite view")
    return dict(summary=out, windows=j)


def run(root: Path = Path("."), out_dir: str = "outputs/fieldtruth_v1") -> dict:
    out = root / out_dir
    out.mkdir(parents=True, exist_ok=True)
    match = pd.read_csv(root / "outputs/insitu_v1/station_lake_match.csv")
    res, _ = load_results(sorted((root / "data/raw/D10_wqp").glob("result_20[2][0-6].csv")))
    fw = field_weeks(res, match)
    # E2 matchups
    obs = load_observations(root / "data/raw/D03_cyan", sorted(match["cyan_objectid"].unique()), 0.5)
    obs = obs[(obs["valid_fraction"] >= 0.5) & obs["start"].dt.year.between(2020, 2025) & obs["start"].dt.month.isin(SEASON)]
    m = obs[["cyan_objectid", "start", "frac_ge_bloom", "median_dn"]].merge(fw, on=["cyan_objectid", "start"])
    m = m.rename(columns={"frac_ge_bloom": "extent"}).dropna(subset=["extent", "log_chl"])
    m["extent"] = m["extent"] * 100
    m["year"], m["month"] = m["start"].dt.year, m["start"].dt.month
    m.to_csv(out / "matchups.csv", index=False)
    res2 = dict(E2_primary=drift(m, "extent"), E2_sens_median_dn=drift(m, "median_dn"))
    ny = m.groupby("cyan_objectid")["year"].nunique()
    bal = m[m["cyan_objectid"].isin(ny[ny >= 5].index)]
    if bal["cyan_objectid"].nunique() >= 10:
        res2["E2_sens_lakes_5of6_years"] = drift(bal, "extent")
    pd.DataFrame(res2["E2_primary"]["year_effects"]).to_csv(out / "drift_year_effects.csv", index=False)
    # E3
    ev = pd.read_parquet(root / "outputs/fl_v1/evaluation_windows.parquet")
    ev["cyan_objectid"] = ev["cyan_objectid"].astype(int)
    ev["valid_start"] = pd.to_datetime(ev["valid_start"])
    for tag, thr in (("E3_primary_12ugL", 12.0), ("E3_sens_20ugL", 20.0)):
        r = field_truth(ev, fw, thr)
        res2[tag] = r["summary"]
        if tag == "E3_primary_12ugL":
            r["windows"][["cyan_objectid", "Lake_name_for_public", "valid_start", "p_epa", "lag1_frac", "lag1_bloom",
                          "label_state", "field_chl", "y_field"]].to_csv(out / "field_truth_windows.csv", index=False)
    (out / "summary.json").write_text(json.dumps(res2, indent=1, default=str))
    return res2


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
