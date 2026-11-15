"""Raw-data acquisition. Every download is saved immutably with a manifest row
(source URL, retrieval time, byte size, SHA-256). Nothing here transforms data.

Usage:  python -m bloom.ingest --config config/sources.yaml
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import yaml

CYAN_DATA = "https://cyan.epa.gov/waterbody/data/"
CYAN_PROPS = "https://cyan.epa.gov/waterbody/properties/"
UA = {"User-Agent": "bloomeconomics-research/0.1 (reproducible research script)"}

MANIFEST_FIELDS = ["evidence_id", "title", "url", "retrieved_at", "local_path",
                   "bytes", "sha256", "license", "original_or_derived", "verification_status", "notes"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


_LOCK = threading.Lock()


def append_manifest(manifest: Path, row: dict) -> None:
    with _LOCK:
        _append_manifest(manifest, row)


def _append_manifest(manifest: Path, row: dict) -> None:
    new = not manifest.exists()
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in MANIFEST_FIELDS})


def fetch_json(url: str, params: dict, retries: int = 4, timeout: int = 240) -> dict:
    """GET JSON, retrying on timeouts/truncation. Raises on persistent failure —
    never returns partial or placeholder data."""
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout)
            r.raise_for_status()
            return r.json()  # raises if truncated / not JSON
        except (requests.RequestException, ValueError) as e:  # noqa: PERF203
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"failed after {retries} attempts: {url} {params}: {last}")


def fetch_cyan_weekly(objectid: int, years: list[int], outdir: Path, manifest: Path) -> list[Path]:
    """Download CyAN weekly-composite DN histograms (256 bins) for one waterbody,
    one calendar year per request (multi-year requests time out server-side)."""
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    props_path = outdir / f"properties_{objectid}.json"
    if not props_path.exists():
        props = fetch_json(CYAN_PROPS, {"OBJECTID": objectid})
        props_path.write_text(json.dumps(props, indent=1))
        append_manifest(manifest, dict(
            evidence_id=f"D03-props-{objectid}", title="CyAN waterbody properties (NHD)",
            url=f"{CYAN_PROPS}?OBJECTID={objectid}", retrieved_at=_now(), local_path=str(props_path),
            bytes=props_path.stat().st_size, sha256=sha256(props_path), license="US Government work",
            original_or_derived="original", verification_status="downloaded"))
    for y in years:
        p = outdir / f"cyan_weekly_{objectid}_{y}.json"
        if p.exists():
            paths.append(p)
            continue
        params = {"OBJECTID": objectid, "start_year": y, "start_day": 1,
                  "end_year": y, "end_day": 366, "daily": "False"}
        try:
            data = fetch_json(CYAN_DATA, params)
        except RuntimeError as e:
            print(f"[ingest] UNAVAILABLE {y}: {e}")
            append_manifest(manifest, dict(evidence_id=f"D03-weekly-{objectid}-{y}", title="CyAN weekly",
                                           url=CYAN_DATA, retrieved_at=_now(),
                                           verification_status="FAILED", notes=str(e)[:300]))
            continue
        tmp = p.with_suffix(".part"); tmp.write_text(json.dumps(data)); tmp.replace(p)  # atomic
        append_manifest(manifest, dict(
            evidence_id=f"D03-weekly-{objectid}-{y}",
            title=f"CyAN weekly composite DN histograms, waterbody {objectid}, {y}",
            url=requests.Request("GET", CYAN_DATA, params=params).prepare().url,
            retrieved_at=_now(), local_path=str(p), bytes=p.stat().st_size, sha256=sha256(p),
            license="US Government work (EPA/NASA/NOAA/USGS CyAN)", original_or_derived="original",
            verification_status="downloaded; product version not reported by API",
            notes=f"{len(data.get('data', {}))} weekly records"))
        print(f"[ingest] {y}: {len(data.get('data', {}))} weeks")
        paths.append(p)
    return paths


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/sources.yaml")
    a = ap.parse_args(argv)
    cfg = yaml.safe_load(open(a.config))
    root = Path(cfg.get("root", "."))
    manifest = root / cfg["manifest"]
    for lake in cfg["lakes"]:
        fetch_cyan_weekly(lake["cyan_objectid"], list(range(lake["start_year"], lake["end_year"] + 1)),
                          root / cfg["raw_dir"] / "D03_cyan", manifest)
    if cfg.get("multi_lake"):
        import pandas as pd
        ml = cfg["multi_lake"]
        m = pd.read_csv(root / ml["lake_map_csv"])
        ids = m.loc[m["status"] == "matched", "cyan_objectid"].astype(int).unique()
        print(f"[ingest] multi-lake: {len(ids)} matched waterbodies")
        # year-major order: test years first so a usable evaluation set exists early
        years = ml.get("year_order") or list(range(ml["start_year"], ml["end_year"] + 1))
        jobs = [(int(oid), y) for y in years for oid in ids]
        with ThreadPoolExecutor(max_workers=ml.get("workers", 6)) as ex:  # modest, polite concurrency
            list(ex.map(lambda j: fetch_cyan_weekly(j[0], [j[1]], root / cfg["raw_dir"] / "D03_cyan", manifest), jobs))


if __name__ == "__main__":
    main()
