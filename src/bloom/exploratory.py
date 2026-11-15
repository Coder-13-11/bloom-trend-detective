"""EXPLORATORY (post hoc, defined after viewing primary results on 2025-26).
Not confirmatory: same test data used to motivate and evaluate. Requires validation on
an untouched season (e.g. 2027) before any claim.
  E1 new-episode onsets: no bloom in any of the previous 4 observed weeks (all known)
  E2 hybrid policy: act if last week bloomed OR EPA p > alpha
"""
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd
from .backtest import cluster_bootstrap
from .economics import relative_economic_value
from .normalize import cyan_weekly_to_observations

MODE = "EXPLORATORY (post hoc) on REAL data — not a confirmatory result"


def prior_k_known_nonbloom(ev, raw="data/raw/D03_cyan", k=4, min_valid_frac=0.5):
    out = []
    for oid, g in ev.groupby("cyan_objectid"):
        o = cyan_weekly_to_observations(sorted(Path(raw).glob(f"cyan_weekly_{oid}_*.json")), str(oid), 1)
        o.loc[o.valid_fraction < min_valid_frac, "label_state"] = "unknown"
        st = dict(zip(o.start, o.label_state))
        for idx, w in zip(g.index, g.valid_start):
            prev = [st.get(w - pd.Timedelta(weeks=j), "unknown") for j in range(1, k + 1)]
            out.append((idx, all(p == "non_bloom" for p in prev)))
    s = pd.Series(dict(out)); return s.reindex(ev.index).fillna(False).astype(bool)


def run(ev_path="outputs/fl_v1_primary/evaluation_windows.parquet", out="outputs/fl_v1_exploratory",
        alphas=(0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3, 0.5), n_boot=1000, seed=20261114):
    Path(out).mkdir(parents=True, exist_ok=True)
    ev = pd.read_parquet(ev_path)
    ev["new_episode_eligible"] = prior_k_known_nonbloom(ev)
    pols = {"EPA_forecast": lambda d, a: d.p_epa.to_numpy() > a,
            "persistence": lambda d, a: d.lag1_state.eq("bloom").to_numpy(),
            "hybrid_persist_or_EPA": lambda d, a: d.lag1_state.eq("bloom").to_numpy() | (d.p_epa.to_numpy() > a)}
    subsets = {"all": ev, "new_episode_onset": ev[ev.new_episode_eligible].reset_index(drop=True)}
    rows, boots = [], []
    for sn, sd in subsets.items():
        y = sd.y.to_numpy(bool)
        for a in alphas:
            for pn, f in pols.items():
                rows.append(dict(subset=sn, alpha=a, policy=pn, n=len(sd), events=int(y.sum()),
                                 rev=relative_economic_value(f(sd, a), y, a)))
            # CI for: hybrid - persistence (all), EPA vs never-act (new episodes; persistence == never here)
            ref = "persistence"
            tgt = "hybrid_persist_or_EPA" if sn == "all" else "EPA_forecast"
            def diff(x, a=a, t=tgt):
                yy = x.y.to_numpy(bool)
                return relative_economic_value(pols[t](x, a), yy, a) - relative_economic_value(pols[ref](x, a), yy, a)
            lo, med, hi = cluster_bootstrap(sd, diff, n_boot, seed)
            boots.append(dict(subset=sn, alpha=a, comparison=f"{tgt} - {ref}", p2_5=lo, median=med, p97_5=hi))
    r, b = pd.DataFrame(rows), pd.DataFrame(boots)
    for name, df in (("rev_curve", r), ("bootstrap", b)):
        df.insert(0, "data_mode", MODE); df.to_csv(f"{out}/{name}.csv", index=False)
    return r, b


if __name__ == "__main__":
    r, b = run()
    print(r.pivot_table(index="alpha", columns=["subset", "policy"], values="rev").round(3).to_string())
    print(r.groupby("subset")[["n", "events"]].first())
    print(b.drop(columns="data_mode").round(3).to_string())
