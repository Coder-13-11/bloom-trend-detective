"""Trend detection (protocol Amendment 2, pre-registered 2026-11-15).

Mann-Kendall test, Sen's slope with a Gilbert (1987) confidence interval, and
Benjamini-Hochberg FDR. Seasonal (May-Oct) lake-year aggregation of CyAN observations.
Descriptive only: no causal links between variables are tested or claimed.
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import norm

from .backtest import load_observations

EXACT_MAX_N = 8


def mk_s(x) -> int:
    x = np.asarray(x, float)
    i, j = np.triu_indices(len(x), 1)
    return int(np.sign(x[j] - x[i]).sum())


def mk_test(x) -> dict:
    """Two-sided Mann-Kendall. Exact permutation p for n <= 8 (ties handled by permuting
    the observed values); otherwise normal approximation with tie-corrected variance."""
    x = np.asarray(x, float)
    n = len(x)
    if n < 3:
        raise ValueError("Mann-Kendall needs n >= 3")
    s = mk_s(x)
    _, t = np.unique(x, return_counts=True)
    var = (n * (n - 1) * (2 * n + 5) - np.sum(t * (t - 1) * (2 * t + 5))) / 18.0
    if var <= 0:  # all values tied
        return dict(n=n, S=s, var_S=0.0, p=1.0, method="all_tied", tau=np.nan)
    tau = s / (0.5 * n * (n - 1))
    if n <= EXACT_MAX_N:
        perms = np.array(list(itertools.permutations(x)))
        i, j = np.triu_indices(n, 1)
        s_perm = np.sign(perms[:, j] - perms[:, i]).sum(axis=1)
        p = float(np.mean(np.abs(s_perm) >= abs(s) - 1e-9))
        return dict(n=n, S=s, var_S=var, p=p, method="exact_permutation", tau=tau)
    z = 0.0 if s == 0 else (s - np.sign(s)) / np.sqrt(var)
    return dict(n=n, S=s, var_S=var, p=float(2 * norm.sf(abs(z))), method="normal_tie_corrected", tau=tau)


def sens_slope(t, x, conf: float = 0.95) -> dict:
    """Sen's slope (median pairwise slope) and Gilbert (1987) rank-based CI."""
    t, x = np.asarray(t, float), np.asarray(x, float)
    i, j = np.triu_indices(len(x), 1)
    ok = t[j] != t[i]
    slopes = np.sort((x[j] - x[i])[ok] / (t[j] - t[i])[ok])
    nn = len(slopes)
    slope = float(np.median(slopes))
    intercept = float(np.median(x - slope * t))
    var = mk_test(x)["var_S"] if len(x) >= 3 else 0.0
    c = norm.ppf(0.5 + conf / 2) * np.sqrt(var)
    m1, m2 = (nn - c) / 2.0, (nn + c) / 2.0
    lo_i, hi_i = int(np.round(m1)) - 1, int(np.round(m2))
    lo = float(slopes[lo_i]) if 0 <= lo_i < nn else np.nan
    hi = float(slopes[hi_i]) if 0 <= hi_i < nn else np.nan
    return dict(slope=slope, intercept=intercept, slope_lo=lo, slope_hi=hi)


def bh_adjust(p) -> np.ndarray:
    p = np.asarray(p, float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(adj, 1.0)
    return out


def lag1_autocorr(resid) -> float:
    r = np.asarray(resid, float) - np.mean(resid)
    d = np.sum(r * r)
    return float(np.sum(r[1:] * r[:-1]) / d) if d > 0 else np.nan


def verdict(p_raw: float, p_adj: float, slope: float, n: int, alpha: float = 0.05) -> str:
    if p_adj < alpha and slope != 0:
        return f"Significant {'upward' if slope > 0 else 'downward'} trend"
    if p_raw < alpha:
        return "Possible trend — not significant after accounting for testing many lakes"
    return f"No clear trend yet (n = {n} seasons)"


def seasonal_lake_years(obs: pd.DataFrame, months=(5, 6, 7, 8, 9, 10), min_valid_frac: float = 0.5,
                        min_known_weeks: int = 13) -> pd.DataFrame:
    """Per lake-year over weeks starting in `months`: V1 bloom-week share and V2 mean extent."""
    o = obs[obs["start"].dt.month.isin(months)].copy()
    o["year"] = o["start"].dt.year
    o["known"] = o["label_state"].isin(["bloom", "non_bloom"]) & (o["valid_fraction"] >= min_valid_frac)
    o["bloom"] = o["known"] & o["label_state"].eq("bloom")
    o["ext"] = o["frac_ge_bloom"].where(o["valid_fraction"] >= min_valid_frac)
    g = o.groupby(["cyan_objectid", "year"]).agg(
        season_weeks=("start", "size"), known_weeks=("known", "sum"),
        bloom_weeks=("bloom", "sum"), extent_mean=("ext", "mean")).reset_index()
    g["bloom_share"] = g["bloom_weeks"] / g["known_weeks"].where(g["known_weeks"] > 0)
    g["year_ok"] = g["known_weeks"] >= min_known_weeks
    return g


def trend_table(ly: pd.DataFrame, value: str, key: str, years: list[int], min_years: int) -> pd.DataFrame:
    rows = []
    for k, g in ly.groupby(key):
        g = g[g["year_ok"] & g["year"].isin(years)].dropna(subset=[value]).sort_values("year")
        base = {key: k, "n_years": len(g)}
        if len(g) < min_years:
            rows.append({**base, "tested": False})
            continue
        mk = mk_test(g[value].to_numpy())
        ss = sens_slope(g["year"].to_numpy(), g[value].to_numpy())
        resid = g[value].to_numpy() - (ss["intercept"] + ss["slope"] * g["year"].to_numpy())
        rows.append({**base, "tested": True, "S": mk["S"], "tau": mk["tau"], "p_raw": mk["p"],
                     "p_method": mk["method"], **ss, "lag1_r": lag1_autocorr(resid),
                     "first_year": int(g["year"].min()), "last_year": int(g["year"].max()),
                     "mean_value": float(g[value].mean())})
    return pd.DataFrame(rows)


def run(cfg: dict) -> dict:
    root = Path(cfg.get("root", "."))
    out = root / cfg["output_dir"]
    out.mkdir(parents=True, exist_ok=True)
    lm = pd.read_csv(root / cfg["lake_map_csv"])
    lm = lm[lm["status"] == "matched"].copy()
    lm["cyan_objectid"] = lm["cyan_objectid"].astype(int)
    obs = load_observations(root / cfg["cyan_raw_dir"], lm["cyan_objectid"].tolist(), cfg["min_valid_fraction"])
    ly = seasonal_lake_years(obs, tuple(cfg["season_months"]), cfg["min_valid_fraction"], cfg["min_known_weeks"])
    years = list(range(cfg["cyan_years"][0], cfg["cyan_years"][1] + 1))
    ly = ly[ly["year"].isin(years)]
    names = lm[["cyan_objectid", "COMID", "name"]]
    res = {}
    for var, col in (("V1_bloom_share", "bloom_share"), ("V2_extent", "extent_mean")):
        t = trend_table(ly, col, "cyan_objectid", years, cfg["min_years"])
        tested = t["tested"].fillna(False).astype(bool)
        t.loc[tested, "p_adj"] = bh_adjust(t.loc[tested, "p_raw"].to_numpy())
        t.loc[tested, "verdict"] = [verdict(r.p_raw, r.p_adj, r.slope, r.n_years) for r in t[tested].itertuples()]
        t.loc[~tested, "verdict"] = "Not tested (too few well-observed seasons)"
        t.insert(0, "variable", var)
        t = names.merge(t, on="cyan_objectid", how="right")
        res[var] = t
    # EXPLORATORY (added after viewing per-lake results): statewide yearly means and pixel
    # accounting, to check whether a coherent statewide shift could be a product artifact.
    o = obs[obs["start"].dt.month.isin(cfg["season_months"])].assign(year=lambda d: d["start"].dt.year)
    o = o[o["year"].isin(years)]
    acct = o.assign(tot_px=o["n_valid"] + o["n_nodata"]).groupby("year").agg(
        median_water_px=("tot_px", "median"), mean_valid_fraction=("valid_fraction", "mean"),
        mean_frac_detect=("frac_detect", "mean"), mean_median_dn=("median_dn", "mean"))
    ok = ly[ly["year_ok"]]
    sw = ok.groupby("year").agg(lakes=("cyan_objectid", "size"), mean_known_weeks=("known_weeks", "mean"),
                                mean_bloom_share=("bloom_share", "mean"), mean_extent=("extent_mean", "mean"))
    sw = sw.join(acct).reset_index()
    sw.insert(0, "data_mode", "EXPLORATORY (post hoc) — lakes are not independent; possible product drift")
    sw.to_csv(out / "statewide_by_year.csv", index=False)
    allt = pd.concat(res.values(), ignore_index=True)
    allt.insert(0, "data_mode", "REAL (CyAN API weekly histograms; protocol Amendment 2)")
    allt.to_csv(out / "trend_cyan.csv", index=False)
    ly.merge(names, on="cyan_objectid").to_csv(out / "cyan_lake_years.csv", index=False)
    summary = {}
    for var, t in res.items():
        tt = t[t["tested"].fillna(False).astype(bool)]
        summary[var] = dict(lakes_tested=int(len(tt)), lakes_not_tested=int((~t["tested"].fillna(False).astype(bool)).sum()),
                            raw_p_lt_05=int((tt["p_raw"] < 0.05).sum()), fdr_sig=int((tt["p_adj"] < 0.05).sum()),
                            fdr_sig_up=int(((tt["p_adj"] < 0.05) & (tt["slope"] > 0)).sum()),
                            fdr_sig_down=int(((tt["p_adj"] < 0.05) & (tt["slope"] < 0)).sum()),
                            slope_pos=int((tt["slope"] > 0).sum()), slope_neg=int((tt["slope"] < 0).sum()),
                            slope_zero=int((tt["slope"] == 0).sum()))
    (out / "trend_cyan_summary.json").write_text(json.dumps(dict(config=cfg, summary=summary), indent=1, default=str))
    return dict(trends=allt, lake_years=ly, summary=summary)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/trends.yaml")
    a = ap.parse_args(argv)
    r = run(yaml.safe_load(Path(a.config).read_text()))
    print(json.dumps(r["summary"], indent=1))


if __name__ == "__main__":
    main()
