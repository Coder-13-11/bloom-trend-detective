"""Transfer scenario: USGS SIR 2024-5091 HABITATS costs/effects (2018 event, 2018 USD)
against EPA forecast probabilities for Lake Okeechobee (2025-26). Explicitly a
TRANSFER SCENARIO: different eras, lake-scale p vs downstream-site damages."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd, yaml
from .economics import break_even_probability

DATA_MODE = "SCENARIO (modeled USGS 2018 costs/effects) x REAL EPA 2025-26 forecast probabilities"

def habitats_table(cfg_path="config/scenarios.yaml") -> pd.DataFrame:
    s = yaml.safe_load(open(cfg_path))["habitats_2018_transfer"]
    rows = []
    for k, v in s["scenarios"].items():
        eL = v["benefit_reported"]
        rows.append(dict(scenario=k, C_musd=v["C"], avoided_damage_eL_musd=eL, ancillary_musd=v["anc"],
                         p_star_no_ancillary=break_even_probability(v["C"], 1.0, eL),
                         p_star_with_ancillary=break_even_probability(v["C"], 1.0, eL + v["anc"]),
                         oracle_net_per_event_no_anc=eL - v["C"],
                         oracle_net_per_event_with_anc=eL + v["anc"] - v["C"]))
    return pd.DataFrame(rows)

def run(forecast_csv="data/raw/D01_forecasts/AllWeeks_CyanForecasts.csv", comid=166757656, out="outputs/scenario"):
    Path(out).mkdir(parents=True, exist_ok=True)
    t = habitats_table()
    f = pd.read_csv(forecast_csv); f = f[f.COMID == comid]
    p = f.Percent_chance_of_cyanoHAB.astype(float) / 100
    t["epa_okeechobee_max_weekly_p_2025_26"] = p.max()
    t["weeks_p_above_pstar_with_anc"] = [int((p > x).sum()) for x in t.p_star_with_ancillary]
    t.insert(0, "data_mode", DATA_MODE)
    t.to_csv(f"{out}/habitats_break_even.csv", index=False)
    return t

if __name__ == "__main__":
    print(run().round(3).to_string())
