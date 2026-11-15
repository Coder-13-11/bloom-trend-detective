"""Retrospective evaluation of the archived EPA weekly cyanoHAB forecast against
simple baselines on identical lake-weeks, plus cost-loss (relative economic value)
curves. Design is prespecified in research/protocol.md; do not tune on test years.

Usage: python -m bloom.backtest --config config/experiment.yaml
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score

from .economics import relative_economic_value
from .normalize import cyan_weekly_to_observations

DATA_MODE = "REAL: EPA archived forecasts (Qlik export) + CyAN API weekly composites"


# ------------------------------------------------------------------ data assembly
def load_observations(raw_dir: Path, objectids, min_valid_frac: float) -> pd.DataFrame:
    out = []
    for oid in objectids:
        paths = sorted(raw_dir.glob(f"cyan_weekly_{oid}_*.json"))
        if not paths:
            continue
        o = cyan_weekly_to_observations(paths, str(oid), min_valid=1)
        # 'unknown' when too little of the lake was observed; never imputed as negative
        o.loc[o["valid_fraction"] < min_valid_frac, "label_state"] = "unknown"
        o["cyan_objectid"] = int(oid)
        out.append(o)
    return pd.concat(out, ignore_index=True)


def load_forecasts(csv: Path, comids) -> pd.DataFrame:
    f = pd.read_csv(csv)
    f = f[f["COMID"].isin(comids)].copy()
    f["valid_start"] = pd.to_datetime(f["Date"].str.split(" to ").str[0], format="%b-%d-%Y")
    f["p_epa"] = f["Percent_chance_of_cyanoHAB"].astype(float) / 100.0
    if ((f.p_epa < 0) | (f.p_epa > 1)).any():
        raise ValueError("invalid EPA probability")
    if f.duplicated(["COMID", "valid_start"]).any():
        raise ValueError("duplicate forecast lake-weeks")
    return f[["COMID", "Lake_name_for_public", "valid_start", "p_epa"]]


def add_lags(obs: pd.DataFrame) -> pd.DataFrame:
    """Lagged *observed* state by exact calendar week (missing weeks stay unknown)."""
    o = obs[["cyan_objectid", "start", "label_state", "median_dn", "frac_ge_bloom"]].copy()
    res = obs.copy()
    for k in (1, 2):
        lag = o.copy()
        lag["start"] = lag["start"] + pd.Timedelta(weeks=k)
        lag = lag.rename(columns={"label_state": f"lag{k}_state", "median_dn": f"lag{k}_dn",
                                  "frac_ge_bloom": f"lag{k}_frac"})
        res = res.merge(lag, on=["cyan_objectid", "start"], how="left")
        res[f"lag{k}_state"] = res[f"lag{k}_state"].fillna("unknown")
    return res


def climatology(train: pd.DataFrame, k: float) -> pd.DataFrame:
    """Lake x month bloom frequency, shrunk to the all-lake month rate (Beta prior, strength k)."""
    t = train[train.label_state != "unknown"].assign(y=lambda d: d.label_state == "bloom",
                                                    month=lambda d: d.start.dt.month)
    region = t.groupby("month").y.mean().rename("m_rate")
    g = t.groupby(["cyan_objectid", "month"]).y.agg(["sum", "count"]).reset_index().merge(region, on="month")
    g["p_clim"] = (g["sum"] + k * g["m_rate"]) / (g["count"] + k)
    return g[["cyan_objectid", "month", "p_clim"]], region


FEATURES = ["lag1_dn_s", "lag1_frac", "lag1_bloom", "sin_w", "cos_w"]


def make_features(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    w = d.start.dt.isocalendar().week.astype(float)
    d["sin_w"], d["cos_w"] = np.sin(2 * np.pi * w / 52.18), np.cos(2 * np.pi * w / 52.18)
    d["lag1_dn_s"] = d["lag1_dn"] / 253.0
    d["lag1_bloom"] = (d["lag1_state"] == "bloom").astype(float)
    return d


# ------------------------------------------------------------------ metrics
def prob_metrics(p, y) -> dict:
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6); y = np.asarray(y, bool)
    m = dict(n=int(y.size), events=int(y.sum()), brier=brier_score_loss(y, p),
             log_loss=log_loss(y, p, labels=[0, 1]), mean_p=float(p.mean()), base_rate=float(y.mean()))
    if 0 < y.sum() < y.size:
        m.update(roc_auc=roc_auc_score(y, p), pr_auc=average_precision_score(y, p))
    return m


def reliability(p, y, bins=(0, .05, .1, .2, .3, .5, .7, 1.0001)) -> pd.DataFrame:
    df = pd.DataFrame(dict(p=p, y=y)); df["bin"] = pd.cut(df.p, bins, right=False)
    return df.groupby("bin", observed=True).agg(n=("y", "size"), mean_p=("p", "mean"), obs_freq=("y", "mean")).reset_index()


def rev_curve(d: pd.DataFrame, alphas, policies: dict) -> pd.DataFrame:
    y = d["y"].to_numpy(bool)
    rows = []
    for a in alphas:
        for name, fn in policies.items():
            rows.append(dict(alpha=a, policy=name, rev=relative_economic_value(fn(d, a), y, a)))
    return pd.DataFrame(rows)


def cluster_bootstrap(d, stat_fn, n_boot, seed, cluster="cyan_objectid"):
    rng = np.random.default_rng(seed)
    groups = {k: v.index.to_numpy() for k, v in d.groupby(cluster)}
    keys = np.array(list(groups))
    vals = []
    for _ in range(n_boot):
        idx = np.concatenate([groups[k] for k in rng.choice(keys, size=keys.size, replace=True)])
        vals.append(stat_fn(d.loc[idx]))
    v = np.array(vals, float)
    return np.nanpercentile(v, [2.5, 50, 97.5])


# ------------------------------------------------------------------ main
def run(cfg: dict) -> dict:
    root = Path(cfg.get("root", "."))
    out = root / cfg["output_dir"]; out.mkdir(parents=True, exist_ok=True)
    lm = pd.read_csv(root / cfg["lake_map_csv"])
    lm = lm[lm.status == "matched"].copy()
    lm["cyan_objectid"] = lm.cyan_objectid.astype(int)
    obs = load_observations(root / cfg["cyan_raw_dir"], lm.cyan_objectid.unique(), cfg["min_valid_fraction"])
    obs = add_lags(obs)
    fc = load_forecasts(root / cfg["forecast_csv"], lm.COMID.unique()).merge(lm[["COMID", "cyan_objectid"]], on="COMID")

    tr_end = pd.Timestamp(cfg["train_end"])
    train = obs[(obs.start <= tr_end) & (obs.start >= pd.Timestamp(cfg.get("train_start", "2000-01-01")))]
    fe = make_features(obs)
    ok = (fe.label_state != "unknown") & (fe.lag1_state != "unknown")
    trn = fe.loc[ok].merge(train[["cyan_objectid", "start"]], on=["cyan_objectid", "start"])
    secondary = cfg.get("secondary_baselines", True) and trn.label_state.eq("bloom").sum() >= 10
    coef = {}
    if secondary:
        clim, region = climatology(train, cfg["clim_prior_strength"])
        lr = LogisticRegression(C=1.0, max_iter=1000).fit(trn[FEATURES], trn.label_state == "bloom")
        coef = dict(zip(FEATURES, lr.coef_[0].round(4).tolist()), intercept=float(lr.intercept_[0]),
                    n_train=int(len(trn)), train_years=sorted(train.start.dt.year.unique().tolist()))
        fe["p_logit"] = np.where(fe.lag1_state != "unknown", lr.predict_proba(fe[FEATURES].fillna(0))[:, 1], np.nan)

    d = fc.merge(fe, left_on=["cyan_objectid", "valid_start"], right_on=["cyan_objectid", "start"], how="left")
    if secondary:
        d["month"] = d.valid_start.dt.month
        d = d.merge(clim, on=["cyan_objectid", "month"], how="left").merge(region, on="month", how="left")
        d["p_clim"] = d.p_clim.fillna(d.m_rate)

    # ---- eligibility audit (identical set for every policy)
    audit = dict(forecast_rows=len(d),
                 no_observation=int(d.label_state.isna().sum()),
                 outcome_unknown=int((d.label_state == "unknown").sum()),
                 lag1_unknown=int(((d.label_state.isin(["bloom", "non_bloom"])) & (d.lag1_state != "bloom") & (d.lag1_state != "non_bloom")).sum()))
    ev = d[d.label_state.isin(["bloom", "non_bloom"]) & d.lag1_state.isin(["bloom", "non_bloom"])
           ].copy().reset_index(drop=True)
    ev["y"] = ev.label_state == "bloom"
    ev["onset_eligible"] = ev.lag1_state == "non_bloom"
    ev["p_persist"] = (ev.lag1_state == "bloom").astype(float)
    audit.update(eligible=len(ev), lakes=int(ev.cyan_objectid.nunique()),
                 events=int(ev.y.sum()), onset_windows=int(ev.onset_eligible.sum()),
                 onsets=int((ev.y & ev.onset_eligible).sum()))

    # Two blocks, each on ONE common set of windows:
    #   primary   = EPA vs persistence (no training needed) on all eligible windows `ev`
    #   secondary = + climatology + logistic, on windows where every baseline is defined `ev2`
    prim = {"EPA_forecast": "p_epa", "persistence": "p_persist"}
    blocks = [("primary", ev, prim)]
    if secondary:
        sec = dict(prim, climatology="p_clim", logistic_lag1="p_logit")
        ev2 = ev[ev.p_clim.notna() & ev.p_logit.notna()].reset_index(drop=True)
        blocks.append(("secondary_common", ev2, sec))
        audit.update(secondary_eligible=len(ev2), secondary_events=int(ev2.y.sum()))
    audit["secondary_baselines"] = bool(secondary)

    metrics, revs = [], []
    alphas = np.round(np.array(cfg["alphas"], float), 4)
    for block, bd, probs in blocks:
        for subset, sd in [("all", bd), ("onset", bd[bd.onset_eligible].reset_index(drop=True))]:
            for yr in ["all"] + sorted(bd.valid_start.dt.year.unique().tolist()):
                s = sd if yr == "all" else sd[sd.valid_start.dt.year == yr]
                if s.empty:
                    continue
                for name, col in probs.items():
                    metrics.append(dict(block=block, subset=subset, year=yr, policy=name, **prob_metrics(s[col], s.y)))
            pol = {n: (lambda c: (lambda dd, a: dd[c].to_numpy() > a))(c) for n, c in probs.items() if n != "persistence"}
            pol["persistence"] = lambda dd, a: dd["lag1_state"].eq("bloom").to_numpy()
            # lag-2 unknown -> no action (a manager without information does not act)
            pol["persistence_lag2"] = lambda dd, a: dd["lag2_state"].eq("bloom").to_numpy()
            revs.append(rev_curve(sd, alphas, pol).assign(block=block, subset=subset))
    metrics, rev = pd.DataFrame(metrics), pd.concat(revs)
    probs = blocks[-1][2]

    # paired bootstrap: REV(EPA) - REV(persistence), clustered by lake
    boot = []
    for subset, sd in [("all", ev), ("onset", ev[ev.onset_eligible].reset_index(drop=True))]:
        for a in cfg["bootstrap_alphas"]:
            def diff(x, a=a):
                y = x.y.to_numpy(bool)
                return (relative_economic_value(x.p_epa.to_numpy() > a, y, a)
                        - relative_economic_value(x.lag1_state.eq("bloom").to_numpy(), y, a))
            lo, med, hi = cluster_bootstrap(sd, diff, cfg["n_boot"], cfg["seed"])
            boot.append(dict(subset=subset, alpha=a, rev_epa_minus_persistence_p2_5=lo, median=med, p97_5=hi))
    boot = pd.DataFrame(boot)

    rb = blocks[-1][1]
    rel = pd.concat([reliability(rb[c], rb.y).assign(policy=n, block=blocks[-1][0])
                     for n, c in probs.items() if n != "persistence"])

    for name, df in [("metrics", metrics), ("rev_curve", rev), ("rev_bootstrap", boot), ("reliability", rel)]:
        df.insert(0, "data_mode", DATA_MODE)
        df.to_csv(out / f"{name}.csv", index=False)
    ev.assign(data_mode=DATA_MODE).to_parquet(out / "evaluation_windows.parquet", index=False)
    manifest = dict(data_mode=DATA_MODE, config=cfg, audit=audit,
                    logistic=coef,
                    python=platform.python_version(),
                    packages={m: __import__(m).__version__ for m in ["pandas", "numpy", "sklearn"]})
    (out / "run_manifest.json").write_text(json.dumps(manifest, indent=1, default=str))
    return dict(audit=audit, metrics=metrics, rev=rev, boot=boot, ev=ev)


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--config", default="config/experiment.yaml")
    a = ap.parse_args(argv)
    r = run(yaml.safe_load(open(a.config)))
    print(json.dumps(r["audit"], indent=1))
    print(r["metrics"][r["metrics"].year == "all"].round(4).to_string())
    print(r["boot"].round(3).to_string())


if __name__ == "__main__":
    main()
