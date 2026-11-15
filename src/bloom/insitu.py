"""Field (in-situ) chlorophyll cross-check of the satellite trend — protocol Amendment 3.

Data: Water Quality Portal narrowResult CSVs (Florida lakes, 'Chlorophyll a, corrected for
pheophytin') and CyAN/NHD lake polygons. Stations are assigned to lakes by point-in-polygon
(150 m tolerance). Nothing here uses or changes the satellite labels.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .trends import bh_adjust, lag1_autocorr, mk_test, sens_slope

UNIT = {"ug/l": 1.0, "mg/m3": 1.0, "ppb": 1.0, "mg/l": 1000.0, "ug/L": 1.0}
SEASON = (5, 6, 7, 8, 9, 10)


# ---------- geometry ----------
def _features(o):
    if isinstance(o, dict):
        if o.get("type") == "Feature" and "geometry" in o:
            yield o
        else:
            for v in o.values():
                yield from _features(v)
    elif isinstance(o, list):
        for v in o:
            yield from _features(v)


def load_exteriors(path: Path) -> list[np.ndarray]:
    """Exterior rings (lon, lat) of every polygon in a CyAN geometry file. Holes ignored."""
    rings = []
    for f in _features(json.loads(Path(path).read_text())):
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"] if g["type"] == "MultiPolygon" else []
        for poly in polys:
            rings.append(np.asarray(poly[0], float)[:, :2])
    return rings


def points_in_ring(lon, lat, ring) -> np.ndarray:
    x, y = np.asarray(lon, float), np.asarray(lat, float)
    xi, yi = ring[:-1, 0], ring[:-1, 1]
    xj, yj = ring[1:, 0], ring[1:, 1]
    inside = np.zeros(len(x), bool)
    for a, b, c, d in zip(xi, yi, xj, yj):
        cond = (b > y) != (d > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            xint = (c - a) * (y - b) / (d - b) + a
        inside ^= cond & (x < xint)
    return inside


def dist_to_ring_m(lon, lat, ring) -> np.ndarray:
    """Min distance (m) from points to ring segments, local equirectangular projection."""
    lat0 = np.deg2rad(np.mean(ring[:, 1]))
    kx, ky = 111320.0 * np.cos(lat0), 110540.0
    px, py = np.asarray(lon, float) * kx, np.asarray(lat, float) * ky
    ax, ay = ring[:-1, 0] * kx, ring[:-1, 1] * ky
    bx, by = ring[1:, 0] * kx, ring[1:, 1] * ky
    best = np.full(len(px), np.inf)
    for a0, a1, b0, b1 in zip(ax, ay, bx, by):
        dx, dy = b0 - a0, b1 - a1
        L2 = dx * dx + dy * dy
        t = np.clip(((px - a0) * dx + (py - a1) * dy) / L2, 0, 1) if L2 > 0 else 0.0
        best = np.minimum(best, np.hypot(px - (a0 + t * dx), py - (a1 + t * dy)))
    return best


def match_stations(stations: pd.DataFrame, geom_dir: Path, oids, tol_m: float = 150.0) -> pd.DataFrame:
    lon, lat = stations["LongitudeMeasure"].to_numpy(float), stations["LatitudeMeasure"].to_numpy(float)
    hits = []
    for oid in oids:
        rings = load_exteriors(geom_dir / f"geom_{oid}.json")
        if not rings:
            continue
        allr = np.vstack(rings)
        pad = 0.003  # ~300 m bbox prefilter
        cand = np.where((lon >= allr[:, 0].min() - pad) & (lon <= allr[:, 0].max() + pad) &
                        (lat >= allr[:, 1].min() - pad) & (lat <= allr[:, 1].max() + pad))[0]
        if not len(cand):
            continue
        ok = np.zeros(len(cand), bool)
        how = np.full(len(cand), "", object)
        for r in rings:
            ins = points_in_ring(lon[cand], lat[cand], r)
            near = ~ins & (dist_to_ring_m(lon[cand], lat[cand], r) <= tol_m)
            how[ins] = "inside"
            how[near & (how == "")] = "within_tol"
            ok |= ins | near
        for i in cand[ok]:
            hits.append(dict(station=stations["MonitoringLocationIdentifier"].iat[i], cyan_objectid=int(oid),
                             how=how[np.where(cand == i)[0][0]], org=stations["OrganizationIdentifier"].iat[i],
                             station_name=stations["MonitoringLocationName"].iat[i]))
    h = pd.DataFrame(hits)
    if h.empty:
        return h
    dup = h.groupby("station")["cyan_objectid"].nunique()
    return h[h["station"].isin(dup[dup == 1].index)].drop_duplicates("station").reset_index(drop=True)


# ---------- field data ----------
def load_results(files) -> tuple[pd.DataFrame, dict]:
    cols = ["OrganizationIdentifier", "ActivityStartDate", "MonitoringLocationIdentifier",
            "ResultDetectionConditionText", "ResultMeasureValue", "ResultMeasure/MeasureUnitCode"]
    d = pd.concat([pd.read_csv(f, usecols=cols, dtype=str, low_memory=False) for f in files], ignore_index=True)
    n0 = len(d)
    d["value"] = pd.to_numeric(d["ResultMeasureValue"], errors="coerce")
    d["factor"] = d["ResultMeasure/MeasureUnitCode"].str.strip().str.lower().map({k.lower(): v for k, v in UNIT.items()})
    audit = dict(rows=n0, non_numeric=int(d["value"].isna().sum()), unknown_unit=int((d["value"].notna() & d["factor"].isna()).sum()),
                 non_positive=int((d["value"] <= 0).sum()))
    d = d[d["value"].notna() & d["factor"].notna() & (d["value"] > 0)].copy()
    d["chl"] = d["value"] * d["factor"]
    d["date"] = pd.to_datetime(d["ActivityStartDate"], errors="coerce")
    d = d.dropna(subset=["date"])
    audit["kept"] = len(d)
    return d.rename(columns={"MonitoringLocationIdentifier": "station"})[["station", "date", "chl", "OrganizationIdentifier"]], audit


def field_lake_years(res: pd.DataFrame, match: pd.DataFrame, min_dates: int = 3, bloom_ugl: float = 12.0) -> pd.DataFrame:
    d = res.merge(match[["station", "cyan_objectid"]], on="station")
    d = d[d["date"].dt.month.isin(SEASON)]
    day = d.groupby(["cyan_objectid", "date"])["chl"].mean().reset_index()
    day["year"] = day["date"].dt.year
    day["log"] = np.log10(day["chl"])
    g = day.groupby(["cyan_objectid", "year"]).agg(n_dates=("chl", "size"), med_log_chl=("log", "median"),
                                                   share_ge12=("chl", lambda s: float((s >= bloom_ugl).mean()))).reset_index()
    g["year_ok"] = g["n_dates"] >= min_dates
    return g


def _slopes(ly: pd.DataFrame, col: str, years, min_years: int) -> pd.DataFrame:
    rows = []
    for oid, g in ly[ly["year_ok"] & ly["year"].isin(years)].dropna(subset=[col]).groupby("cyan_objectid"):
        if len(g) >= min_years:
            g = g.sort_values("year")
            ss = sens_slope(g["year"].to_numpy(), g[col].to_numpy())
            rows.append(dict(cyan_objectid=oid, slope=ss["slope"], n=len(g), p=mk_test(g[col].to_numpy())["p"]))
    return pd.DataFrame(rows)


def _boot_median(x, n_boot, rng):
    x = np.asarray(x, float)
    b = np.median(x[rng.integers(0, len(x), (n_boot, len(x)))], axis=1)
    return float(np.median(x)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def compare(field: pd.DataFrame, sat: pd.DataFrame, years, min_years: int, n_boot: int = 2000, seed: int = 20261115) -> dict:
    fs = _slopes(field, "med_log_chl", years, min_years).rename(columns={"slope": "field_slope", "n": "n_field", "p": "p_field"})
    ss = _slopes(sat, "extent_mean", years, min_years).rename(columns={"slope": "sat_slope", "n": "n_sat", "p": "p_sat"})
    j = fs.merge(ss, on="cyan_objectid")
    rng = np.random.default_rng(seed)
    out = dict(years=[int(min(years)), int(max(years))], lakes=int(len(j)))
    if len(j) < 20:
        out["verdict"] = "Inconclusive (fewer than 20 lakes qualify)"
        return dict(summary=out, lakes=j)
    j["field_pct_per_year"] = (10 ** j["field_slope"] - 1) * 100
    m, lo, hi = _boot_median(j["field_pct_per_year"], n_boot, rng)
    out["P1_field_median_pct_per_year"] = dict(median=m, lo=lo, hi=hi)
    m2, lo2, hi2 = _boot_median(j["sat_slope"] * 100, n_boot, rng)
    out["P1_sat_median_pts_per_year"] = dict(median=m2, lo=lo2, hi=hi2)
    out["field_slope_signs"] = dict(pos=int((j.field_slope > 0).sum()), neg=int((j.field_slope < 0).sum()), zero=int((j.field_slope == 0).sum()))
    out["sat_slope_signs"] = dict(pos=int((j.sat_slope > 0).sum()), neg=int((j.sat_slope < 0).sum()), zero=int((j.sat_slope == 0).sum()))
    rho = spearmanr(j["sat_slope"], j["field_slope"]).statistic
    idx = rng.integers(0, len(j), (n_boot, len(j)))
    rb = [spearmanr(j["sat_slope"].to_numpy()[i], j["field_slope"].to_numpy()[i]).statistic for i in idx]
    out["P2_spearman_slopes"] = dict(rho=float(rho), lo=float(np.nanpercentile(rb, 2.5)), hi=float(np.nanpercentile(rb, 97.5)))
    # P3 within-lake interannual tracking
    f = field[field["year_ok"] & field["year"].isin(years)][["cyan_objectid", "year", "med_log_chl"]]
    s = sat[sat["year_ok"] & sat["year"].isin(years)][["cyan_objectid", "year", "extent_mean"]]
    b = f.merge(s, on=["cyan_objectid", "year"])
    b = b[b["cyan_objectid"].isin(j["cyan_objectid"])]
    r3 = []
    for oid, g in b.groupby("cyan_objectid"):
        if len(g) >= min_years and g["extent_mean"].nunique() > 1 and g["med_log_chl"].nunique() > 1:
            r3.append(dict(cyan_objectid=oid, rho_within=spearmanr(g["extent_mean"], g["med_log_chl"]).statistic))
    r3 = pd.DataFrame(r3)
    j = j.merge(r3, on="cyan_objectid", how="left")
    if len(r3):
        m3, lo3, hi3 = _boot_median(r3["rho_within"], n_boot, rng)
        out["P3_within_lake_rho"] = dict(median=m3, lo=lo3, hi=hi3, share_positive=float((r3.rho_within > 0).mean()), lakes=int(len(r3)))
    field_up = lo > 0
    sat_up = lo2 > 0
    assoc = (out["P2_spearman_slopes"]["lo"] > 0) or (out.get("P3_within_lake_rho", {}).get("lo", -1) > 0)
    if field_up and assoc:
        out["verdict"] = "Corroborated: field chlorophyll also rose, and field and satellite agree"
    elif field_up:
        out["verdict"] = "Partly corroborated: field chlorophyll rose, but lake-level agreement is not shown"
    elif sat_up:
        out["verdict"] = "Not corroborated: the satellite signal rose but field chlorophyll did not"
    else:
        out["verdict"] = "Neither series shows a clear rise on these lakes and years"
    return dict(summary=out, lakes=j)


def time_to_detect(sat: pd.DataFrame, years, min_years: int) -> pd.DataFrame:
    """Weatherhead et al. (1998) years of record needed to detect each lake's V2 trend."""
    rows = []
    for oid, g in sat[sat["year_ok"] & sat["year"].isin(years)].dropna(subset=["extent_mean"]).groupby("cyan_objectid"):
        if len(g) < min_years:
            continue
        g = g.sort_values("year")
        t, x = g["year"].to_numpy(float), g["extent_mean"].to_numpy(float)
        ss = sens_slope(t, x)
        resid = x - (ss["intercept"] + ss["slope"] * t)
        sd = float(np.std(resid, ddof=1))
        phi = float(np.clip(np.nan_to_num(lag1_autocorr(resid)), 0, 0.9))
        w = abs(ss["slope"])
        n_star = float((3.3 * sd / w * np.sqrt((1 + phi) / (1 - phi))) ** (2 / 3)) if w > 0 and sd > 0 else np.nan
        rows.append(dict(cyan_objectid=oid, slope=ss["slope"], resid_sd=sd, phi=phi, n_have=len(g), n_star_years=n_star))
    return pd.DataFrame(rows)


def run(root: Path = Path("."), out_dir: str = "outputs/insitu_v1") -> dict:
    out = root / out_dir
    out.mkdir(parents=True, exist_ok=True)
    wqp = root / "data/raw/D10_wqp"
    lm = pd.read_csv(root / "data/interim/fl_lake_map.csv")
    lm = lm[lm["status"] == "matched"].copy()
    lm["cyan_objectid"] = lm["cyan_objectid"].astype(int)
    st = pd.read_csv(wqp / "stations.csv", dtype=str, low_memory=False)
    st["LatitudeMeasure"] = pd.to_numeric(st["LatitudeMeasure"], errors="coerce")
    st["LongitudeMeasure"] = pd.to_numeric(st["LongitudeMeasure"], errors="coerce")
    st = st.dropna(subset=["LatitudeMeasure", "LongitudeMeasure"]).drop_duplicates("MonitoringLocationIdentifier")
    match = match_stations(st, root / "data/raw/D11_lake_geom", lm["cyan_objectid"].tolist())
    match = match.merge(lm[["cyan_objectid", "name", "COMID"]], on="cyan_objectid")
    match.to_csv(out / "station_lake_match.csv", index=False)
    files = sorted(wqp.glob("result_*.csv"))
    res, audit = load_results(files)
    audit["files"] = [f.name for f in files]
    audit["stations_total"] = int(len(st))
    audit["stations_matched"] = int(len(match))
    audit["lakes_with_station"] = int(match["cyan_objectid"].nunique())
    in_lakes = res[res["station"].isin(match["station"])]
    audit["records_in_matched_lakes"] = int(len(in_lakes))
    audit["records_in_matched_lakes_2020_2025_season"] = int((in_lakes["date"].dt.year.between(2020, 2025) & in_lakes["date"].dt.month.isin(SEASON)).sum())
    field = field_lake_years(res, match)
    field = field.merge(lm[["cyan_objectid", "name"]], on="cyan_objectid")
    field.to_csv(out / "field_lake_years.csv", index=False)
    sat = pd.read_csv(root / "outputs/trends_v1/cyan_lake_years.csv")
    results = {}
    for tag, years, my in (("primary_2020_2025", list(range(2020, 2026)), 5), ("sensitivity_2020_2026", list(range(2020, 2027)), 6)):
        c = compare(field, sat, years, my)
        results[tag] = c["summary"]
        c["lakes"].merge(lm[["cyan_objectid", "name"]], on="cyan_objectid").to_csv(out / f"lake_slopes_{tag}.csv", index=False)
    # secondary: statewide by year on the primary lake set
    prim = pd.read_csv(out / "lake_slopes_primary_2020_2025.csv")
    keep = prim["cyan_objectid"] if "cyan_objectid" in prim else []
    f = field[field["year_ok"] & field["cyan_objectid"].isin(keep) & field["year"].between(2020, 2026)]
    s = sat[sat["year_ok"] & sat["cyan_objectid"].isin(keep) & sat["year"].between(2020, 2026)]
    sw = f.groupby("year").agg(field_lakes=("cyan_objectid", "nunique"), field_mean_dates=("n_dates", "mean"),
                               field_geomean_chl=("med_log_chl", lambda v: float(10 ** v.mean())),
                               field_share_ge12=("share_ge12", "mean")).join(
        s.groupby("year").agg(sat_lakes=("cyan_objectid", "nunique"), sat_bloom_share=("bloom_share", "mean"),
                              sat_extent=("extent_mean", "mean"))).reset_index()
    sw.insert(0, "data_mode", "REAL (WQP field chlorophyll vs CyAN; same lakes; secondary/descriptive)")
    sw.to_csv(out / "statewide_field_vs_satellite.csv", index=False)
    # secondary: long-record field trends
    yrs = sorted(int(p.stem.split("_")[1]) for p in files)
    lr = []
    for oid, g in field[field["year_ok"] & (field["year"] <= 2025)].groupby("cyan_objectid"):
        if len(g) >= 15:
            g = g.sort_values("year")
            mk, ss = mk_test(g["med_log_chl"].to_numpy()), sens_slope(g["year"].to_numpy(), g["med_log_chl"].to_numpy())
            lr.append(dict(cyan_objectid=oid, n_years=len(g), first_year=int(g.year.min()), last_year=int(g.year.max()),
                           pct_per_year=(10 ** ss["slope"] - 1) * 100, pct_lo=(10 ** ss["slope_lo"] - 1) * 100,
                           pct_hi=(10 ** ss["slope_hi"] - 1) * 100, p_raw=mk["p"], slope=ss["slope"], intercept=ss["intercept"]))
    lr = pd.DataFrame(lr)
    if len(lr):
        lr["p_adj"] = bh_adjust(lr["p_raw"].to_numpy())
        lr = lr.merge(lm[["cyan_objectid", "name"]], on="cyan_objectid")
        lr.to_csv(out / "field_long_record_trends.csv", index=False)
        results["long_record"] = dict(years_available=[min(yrs), max(yrs)], lakes=int(len(lr)),
                                      sig_up=int(((lr.p_adj < .05) & (lr.slope > 0)).sum()),
                                      sig_down=int(((lr.p_adj < .05) & (lr.slope < 0)).sum()),
                                      median_pct_per_year=float(lr.pct_per_year.median()))
    # descriptive: per-lake field trend for the public tool (all well-sampled seasons 2000-2025, >= 6 seasons)
    ft = []
    for oid, g in field[field["year_ok"] & (field["year"] <= 2025)].groupby("cyan_objectid"):
        if len(g) >= 6:
            g = g.sort_values("year")
            mk, ss = mk_test(g["med_log_chl"].to_numpy()), sens_slope(g["year"].to_numpy(), g["med_log_chl"].to_numpy())
            ft.append(dict(cyan_objectid=oid, n_years=len(g), first_year=int(g.year.min()), last_year=int(g.year.max()),
                           slope=ss["slope"], intercept=ss["intercept"], slope_lo=ss["slope_lo"], slope_hi=ss["slope_hi"],
                           p_raw=mk["p"], p_method=mk["method"]))
    ft = pd.DataFrame(ft)
    ft["p_adj"] = bh_adjust(ft["p_raw"].to_numpy())
    ft.to_csv(out / "field_trends_tool.csv", index=False)
    results["field_tool_trends"] = dict(lakes=int(len(ft)), fdr_sig_up=int(((ft.p_adj < .05) & (ft.slope > 0)).sum()),
                                        fdr_sig_down=int(((ft.p_adj < .05) & (ft.slope < 0)).sum()))
    # exploratory: balanced panel (all six seasons in both records)
    f6 = field[field["year_ok"] & field["year"].between(2020, 2025)]
    s6 = sat[sat["year_ok"] & sat["year"].between(2020, 2025)]
    full = set(f6.groupby("cyan_objectid")["year"].nunique().loc[lambda x: x == 6].index) & \
        set(s6.groupby("cyan_objectid")["year"].nunique().loc[lambda x: x == 6].index)
    bp = f6[f6["cyan_objectid"].isin(full)].groupby("year").agg(
        field_geomean_chl=("med_log_chl", lambda v: float(10 ** v.mean())), field_share_ge12=("share_ge12", "mean"),
        field_mean_dates=("n_dates", "mean")).join(
        s6[s6["cyan_objectid"].isin(full)].groupby("year").agg(sat_bloom_share=("bloom_share", "mean"), sat_extent=("extent_mean", "mean"))).reset_index()
    bp.insert(0, "lakes", len(full))
    bp.insert(0, "data_mode", "EXPLORATORY (post hoc): lakes with all six seasons in both records")
    bp.to_csv(out / "balanced_panel_by_year.csv", index=False)
    ttd = time_to_detect(sat, list(range(2020, 2027)), 6).merge(lm[["cyan_objectid", "name"]], on="cyan_objectid")
    ttd.to_csv(out / "time_to_detect.csv", index=False)
    results["time_to_detect"] = dict(lakes=int(ttd["n_star_years"].notna().sum()), median_years=float(ttd["n_star_years"].median()),
                                     share_need_more_than_7=float((ttd["n_star_years"] > 7).mean()))
    results["audit"] = audit
    (out / "summary.json").write_text(json.dumps(results, indent=1, default=str))
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    a = ap.parse_args()
    print(json.dumps(run(Path(a.root)), indent=1, default=str))
