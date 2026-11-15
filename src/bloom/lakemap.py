"""Map EPA forecast COMIDs to CyAN waterbody OBJECTIDs by name search + centroid
distance. Every match records its distance; ambiguous/unmatched lakes are kept
with status so exclusions are auditable (no silent drops)."""
from __future__ import annotations
import math, re, time
import pandas as pd, requests

SEARCH = "https://cyan.epa.gov/waterbody/search/"

def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(math.sqrt(a))

def clean_name(n: str) -> str:
    return re.sub(r"\s*\(.*?\)\s*", " ", n).strip()

def match_lakes(forecast_lakes: pd.DataFrame, state: str) -> pd.DataFrame:
    rows = []
    for _, L in forecast_lakes.iterrows():
        q = clean_name(L.Lake_name_for_public)
        try:
            r = requests.get(SEARCH, params={"name": q}, timeout=60).json().get("waterbodies", [])
        except Exception as e:  # recorded, not swallowed
            rows.append(dict(COMID=L.COMID, name=L.Lake_name_for_public, status=f"search_error:{e}"[:120])); continue
        if not isinstance(r, list): r = []
        cands = [w for w in r if isinstance(w, dict) and w.get("state_abbr") == state]
        best = None
        for w in cands:
            d = haversine_km(L.Lat_centroid, L.Lon_centroid, w["centroid_lat"], w["centroid_lng"])
            if best is None or d < best[0]: best = (d, w)
        if best is None:
            rows.append(dict(COMID=L.COMID, name=L.Lake_name_for_public, status="no_candidate")); continue
        d, w = best
        tol = max(3.0, 0.6*math.sqrt(w["areasqkm"]))  # centroid conventions differ; scale with lake size
        rows.append(dict(COMID=L.COMID, name=L.Lake_name_for_public, cyan_objectid=w["objectid"],
                         cyan_name=w["name"], cyan_area_km2=w["areasqkm"], dist_km=round(d, 3),
                         tol_km=round(tol, 2), n_candidates=len(cands),
                         status="matched" if d <= tol else "too_far"))
        time.sleep(0.3)
    return pd.DataFrame(rows)
