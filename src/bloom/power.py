"""NASA POWER (MERRA-2) warm-season temperature and rainfall trends at lake centroids.

Protocol Amendment 2, V3. Source: NASA POWER monthly point API (no key needed);
header 'sources' is recorded per file. Values are reanalysis at a coarse grid cell,
not satellite measurements of the lake.
"""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .ingest import append_manifest, fetch_json, sha256
from .trends import lag1_autocorr, mk_test, sens_slope

POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"


def lake_centroids(lake_map_csv: Path, forecast_csv: Path) -> pd.DataFrame:
    lm = pd.read_csv(lake_map_csv)
    lm = lm[lm["status"] == "matched"].copy()
    f = pd.read_csv(forecast_csv, usecols=["COMID", "Lat_centroid", "Lon_centroid"]).drop_duplicates("COMID")
    return lm.merge(f, on="COMID", how="left")[["COMID", "name", "cyan_objectid", "Lat_centroid", "Lon_centroid"]]


def fetch_power(comid: int, lat: float, lon: float, cfg: dict, outdir: Path, manifest: Path) -> Path:
    path = outdir / f"power_monthly_{comid}.json"
    if path.exists():
        return path
    params = dict(parameters=",".join(cfg["parameters"]), community=cfg["community"],
                  latitude=round(lat, 4), longitude=round(lon, 4),
                  start=cfg["years"][0], end=cfg["years"][1], format="JSON")
    d = fetch_json(POWER_URL, params)
    if "properties" not in d:
        raise RuntimeError(f"POWER returned no data for COMID {comid}: {d.get('messages')}")
    tmp = path.with_suffix(".part")
    tmp.write_text(json.dumps(d))
    tmp.rename(path)
    append_manifest(manifest, dict(
        evidence_id=f"D09-power-{comid}", title=f"NASA POWER monthly {cfg['parameters']} (MERRA-2), COMID {comid}",
        url=POWER_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items()),
        retrieved_at=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), local_path=str(path),
        bytes=path.stat().st_size, sha256=sha256(path), license="NASA POWER (public, cite NASA LaRC POWER)",
        original_or_derived="original", verification_status="downloaded",
        notes=f"sources={d.get('header', {}).get('sources')}"))
    return path


def warm_season(path: Path, months=(5, 6, 7, 8, 9, 10)) -> pd.DataFrame:
    d = json.loads(Path(path).read_text())
    p = d["properties"]["parameter"]
    units = {k: v["units"] for k, v in d["parameters"].items()}
    if units.get("PRECTOTCORR") != "mm/day" or units.get("T2M") != "C":
        raise ValueError(f"unexpected POWER units {units}")
    fill = d["header"].get("fill_value", -999.0)
    rows = []
    for key in p["T2M"]:
        y, m = int(key[:4]), int(key[4:])
        if m in months:
            t, r = p["T2M"][key], p["PRECTOTCORR"][key]
            rows.append(dict(year=y, month=m, t2m=np.nan if t == fill else t,
                             rain_mm=np.nan if r == fill else r * calendar.monthrange(y, m)[1]))
    m = pd.DataFrame(rows)
    full = m.groupby("year").filter(lambda g: len(g) == len(months) and g[["t2m", "rain_mm"]].notna().all().all())
    return full.groupby("year").agg(t2m_mean=("t2m", "mean"), rain_total_mm=("rain_mm", "sum")).reset_index()


def run(cfg: dict) -> dict:
    root = Path(cfg.get("root", "."))
    pc = cfg["power"]
    raw = root / pc["raw_dir"]
    raw.mkdir(parents=True, exist_ok=True)
    out = root / cfg["output_dir"]
    out.mkdir(parents=True, exist_ok=True)
    lakes = lake_centroids(root / cfg["lake_map_csv"], root / cfg["forecast_csv"])
    manifest = root / "docs/source_manifest.csv"
    with ThreadPoolExecutor(pc.get("workers", 4)) as ex:
        paths = list(ex.map(lambda r: fetch_power(int(r.COMID), r.Lat_centroid, r.Lon_centroid, pc, raw, manifest),
                            lakes.itertuples()))
    series, rows = [], []
    for r, path in zip(lakes.itertuples(), paths):
        ws = warm_season(path)
        ws.insert(0, "COMID", int(r.COMID))
        series.append(ws)
        for var, col, unit in (("V3_t2m", "t2m_mean", "C"), ("V3_rain", "rain_total_mm", "mm")):
            x, t = ws[col].to_numpy(), ws["year"].to_numpy()
            mk, ss = mk_test(x), sens_slope(t, x)
            resid = x - (ss["intercept"] + ss["slope"] * t)
            r1 = lag1_autocorr(resid)
            rows.append(dict(COMID=int(r.COMID), name=r.name, variable=var, unit=unit, n_years=len(x),
                             first_year=int(t.min()), last_year=int(t.max()), S=mk["S"], tau=mk["tau"],
                             p_raw=mk["p"], p_method=mk["method"], **ss,
                             slope_per_decade=ss["slope"] * 10, lo_per_decade=ss["slope_lo"] * 10,
                             hi_per_decade=ss["slope_hi"] * 10, mean_value=float(np.mean(x)), lag1_r=r1,
                             autocorr_flag=bool(abs(r1) > 2 / np.sqrt(len(x)))))
    t = pd.DataFrame(rows)
    t["verdict"] = [("Significant " + ("upward" if s > 0 else "downward") + " trend") if p < 0.05 and s != 0
                    else f"No clear trend (n = {n} seasons)" for p, s, n in zip(t.p_raw, t.slope, t.n_years)]
    s = pd.concat(series, ignore_index=True)
    sig = s.groupby("COMID")[["t2m_mean", "rain_total_mm"]].apply(lambda g: hash(tuple(np.round(g.to_numpy().ravel(), 4))))
    distinct = int(sig.nunique())
    t.insert(0, "data_mode", "REAL (NASA POWER / MERRA-2 reanalysis; protocol Amendment 2 V3)")
    t.to_csv(out / "trend_merra2.csv", index=False)
    s.to_csv(out / "merra2_warm_season.csv", index=False)
    summ = {v: dict(sig_up=int(((g.p_raw < .05) & (g.slope > 0)).sum()), sig_down=int(((g.p_raw < .05) & (g.slope < 0)).sum()),
                    n=int(len(g)), median_slope_per_decade=float(g.slope_per_decade.median()),
                    autocorr_flagged=int(g.autocorr_flag.sum())) for v, g in t.groupby("variable")}
    summ["distinct_power_series"] = distinct
    (out / "trend_merra2_summary.json").write_text(json.dumps(summ, indent=1))
    return dict(trends=t, series=s, summary=summ)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/trends.yaml")
    a = ap.parse_args(argv)
    print(json.dumps(run(yaml.safe_load(Path(a.config).read_text()))["summary"], indent=1))


if __name__ == "__main__":
    main()
