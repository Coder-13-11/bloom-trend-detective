"""Export precomputed results to site/data/site.json for the static picker page.
Reads only pipeline outputs; computes nothing new except formatting."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import load_observations


def _r(x, k=4):
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return None
    return round(float(x), k)


def build(root: Path = Path("."), out: Path = Path("site/data/site.json")) -> dict:
    tr = root / "outputs/trends_v1"
    tc = pd.read_csv(tr / "trend_cyan.csv")
    tm = pd.read_csv(tr / "trend_merra2.csv")
    ly = pd.read_csv(tr / "cyan_lake_years.csv")
    ws = pd.read_csv(tr / "merra2_warm_season.csv")
    sw = pd.read_csv(tr / "statewide_by_year.csv")
    fc = pd.read_csv(root / "data/raw/D01_forecasts/AllWeeks_CyanForecasts.csv",
                     usecols=["COMID", "Lat_centroid", "Lon_centroid"]).drop_duplicates("COMID")
    lm = pd.read_csv(root / "data/interim/fl_lake_map.csv")
    lm = lm[lm.status == "matched"].merge(fc, on="COMID", how="left")
    obs = load_observations(root / "data/raw/D03_cyan", lm.cyan_objectid.astype(int).tolist(), 0.5)

    def trend_obj(r):
        if not bool(r.get("tested", True)) or pd.isna(r.get("slope")):
            return dict(tested=False, verdict=r.get("verdict"))
        return dict(tested=True, slope=_r(r["slope"], 5), lo=_r(r["slope_lo"], 5), hi=_r(r["slope_hi"], 5),
                    intercept=_r(r["intercept"], 5), p=_r(r["p_raw"], 5), p_adj=_r(r.get("p_adj", r["p_raw"]), 5),
                    n=int(r["n_years"]), verdict=r["verdict"], method=r["p_method"])

    ins = root / "outputs/insitu_v1"
    fly = pd.read_csv(ins / "field_lake_years.csv")
    fly = fly[fly.year_ok & (fly.year <= 2025)]
    ftt = pd.read_csv(ins / "field_trends_tool.csv")
    xl = pd.read_csv(ins / "lake_slopes_primary_2020_2025.csv")
    from .trends import verdict as _verdict

    lakes = []
    for r in lm.sort_values("name").itertuples():
        oid, comid = int(r.cyan_objectid), int(r.COMID)
        y = ly[ly.cyan_objectid == oid].sort_values("year")
        w = ws[ws.COMID == comid].sort_values("year")
        o = obs[obs.cyan_objectid == oid].sort_values("start")
        t = {}
        for var in ("V1_bloom_share", "V2_extent"):
            row = tc[(tc.cyan_objectid == oid) & (tc.variable == var)]
            t[var] = trend_obj(row.iloc[0].to_dict()) if len(row) else dict(tested=False)
        for var in ("V3_t2m", "V3_rain"):
            row = tm[(tm.COMID == comid) & (tm.variable == var)]
            t[var] = trend_obj(row.iloc[0].to_dict()) if len(row) else dict(tested=False)
        fy = fly[fly.cyan_objectid == oid].sort_values("year")
        fr = ftt[ftt.cyan_objectid == oid]
        if len(fr):
            q = fr.iloc[0]
            t["V5_field"] = dict(tested=True, slope=_r(q.slope, 6), lo=_r(q.slope_lo, 6), hi=_r(q.slope_hi, 6),
                                 intercept=_r(q.intercept, 5), p=_r(q.p_raw, 5), p_adj=_r(q.p_adj, 5), n=int(q.n_years),
                                 verdict=_verdict(q.p_raw, q.p_adj, q.slope, int(q.n_years)), method=q.p_method,
                                 first=int(q.first_year), last=int(q.last_year))
        else:
            t["V5_field"] = dict(tested=False, verdict="Not tested (too few well-sampled seasons)" if len(fy) else "No field samples matched to this lake")
        xr = xl[xl.cyan_objectid == oid]
        xc = None
        if len(xr):
            q = xr.iloc[0]
            su, fu = q.sat_slope > 0, q.field_slope > 0
            xc = dict(sat_pts=_r(q.sat_slope * 100, 2), field_pct=_r(q.field_pct_per_year, 1),
                      rho=_r(q.rho_within, 2) if pd.notna(q.rho_within) else None,
                      direction=("Both records point up" if su and fu else "Satellite up, field not" if su else
                                 "Field up, satellite not" if fu else "Neither record points up"))
        lakes.append(dict(
            field=dict(year=fy.year.astype(int).tolist(), chl=[_r(10 ** v, 2) for v in fy.med_log_chl], n=fy.n_dates.astype(int).tolist()),
            xcheck=xc,
            comid=comid, oid=oid, name=r.name, lat=_r(r.Lat_centroid), lon=_r(r.Lon_centroid),
            area_km2=_r(r.cyan_area_km2, 2),
            cyan=dict(year=y.year.tolist(), bloom_share=[_r(v) for v in y.bloom_share],
                      extent=[_r(v) for v in y.extent_mean], known=y.known_weeks.astype(int).tolist(),
                      ok=y.year_ok.astype(bool).tolist()),
            weekly=dict(start=o.start.dt.strftime("%Y-%m-%d").tolist(),
                        extent=[_r(v, 3) if vf >= 0.5 else None for v, vf in zip(o.frac_ge_bloom, o.valid_fraction)],
                        state=[{"bloom": 1, "non_bloom": 0}.get(s) for s in o.label_state]),
            merra=dict(year=w.year.tolist(), t2m=[_r(v, 3) for v in w.t2m_mean], rain=[_r(v, 1) for v in w.rain_total_mm]),
            trends=t))

    rc = pd.read_csv(root / "outputs/fl_v1_primary/rev_curve.csv")
    rb = pd.read_csv(root / "outputs/fl_v1_primary/rev_bootstrap.csv")
    rev = {}
    for sub in ("all", "onset"):
        d = rc[(rc.subset == sub) & (rc.block == "primary")]
        rev[sub] = {p: dict(alpha=g.alpha.tolist(), rev=[_r(v) for v in g.rev])
                    for p, g in d.groupby("policy")}
    boot = rb.rename(columns={"rev_epa_minus_persistence_p2_5": "lo", "p97_5": "hi"})[["subset", "alpha", "lo", "median", "hi"]]
    met = pd.read_csv(root / "outputs/fl_v1_primary/metrics.csv")

    summ = dict(cyan=json.loads((tr / "trend_cyan_summary.json").read_text())["summary"],
                merra=json.loads((tr / "trend_merra2_summary.json").read_text()))
    isum = json.loads((ins / "summary.json").read_text())
    fsum = json.loads((root / "outputs/fieldtruth_v1/summary.json").read_text())
    bp = pd.read_csv(ins / "balanced_panel_by_year.csv").drop(columns="data_mode")
    cross = dict(primary=isum["primary_2020_2025"], audit=isum["audit"], field_tool=isum["field_tool_trends"],
                 long_record=isum.get("long_record"), balanced=bp.round(4).to_dict("list"),
                 drift={k: fsum["E2_primary"][k] for k in ("n_matchups", "lakes", "year_slope", "year_effects", "verdict")},
                 drift_sens_dn=fsum["E2_sens_median_dn"]["year_slope"],
                 e3=fsum["E3_primary_12ugL"], e3_sens=fsum["E3_sens_20ugL"])
    site = dict(cross=cross, lakes=lakes, statewide=sw.drop(columns="data_mode").round(4).to_dict("list"),
                rev=rev, rev_boot=boot.round(4).to_dict("records"),
                metrics=met.round(4).to_dict("records"), summary=summ)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(site, separators=(",", ":")))
    return site


if __name__ == "__main__":
    s = build()
    print(len(s["lakes"]), "lakes;", Path("site/data/site.json").stat().st_size // 1024, "KB")
