# Results: trends v1 (protocol Amendment 2), generated 2026-11-15

Code: `src/bloom/trends.py`, `src/bloom/power.py`. Config: `config/trends.yaml`. Output: `outputs/trends_v1/`.
Reproduce in about 30 s from cached data:
```
PYTHONPATH=src python -m bloom.trends
PYTHONPATH=src python -m bloom.power
```

## Confirmatory (pre-registered)
**V1: bloom-week share.**
- Lakes tested: 119; 2 not tested because they had too few seasons with ≥ 13 clear weeks.
- Raw p < 0.05: 20 lakes.
- Significant after Benjamini–Hochberg: **2 lakes, both upward** (Eagle Lake p_adj 0.047, Lake Ariana p_adj 0.047). None downward.
- Sen-slope signs: 45 positive, 1 negative, 73 zero.
- Lake Okeechobee: slope 0, p 0.88. No clear trend.

**V2: bloom extent.**
- Raw p < 0.05: 25 lakes.
- Significant after BH: **10 lakes, all upward.** None downward.
- Sen-slope signs: 81 positive, 6 negative, 32 zero.

**V3: NASA MERRA-2 (POWER), May–October, 1981–2025, n = 45.**
- Temperature: **significant warming at all 121 lakes**, from only 26 distinct POWER series.
  - Median +0.28 °C per decade (range 0.19–0.36).
  - Okeechobee: +0.30 °C per decade [0.20, 0.39].
  - No residual autocorrelation flags.
- Rainfall: 5 of 121 lakes significant upward. Median +2.2 mm per decade.
  - Okeechobee: −5.9 mm per decade, p 0.63.

## Exploratory (post hoc, `statewide_by_year.csv`)
Average across lakes of the May–October bloom-week share, by year:

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| 0.109 | 0.124 | 0.171 | 0.221 | 0.226 | 0.262 | 0.300 |

- The mean lake-median DN rose from 26 to 58.
- The median count of water pixels per lake is constant at 90, so the lake masks did not change.

**Interpretation.** The coherent statewide rise could be real. It could also be a product artifact: sensor drift, a processing-version change, or a change in which Sentinel-3 satellite is used. The API reports no product version. Lakes share weather, so they are not independent, and the sign asymmetry (45 positive vs 1 negative) is not a valid test of anything.

**Cannot be resolved without independent data:** FDEP or LakeWatch field chlorophyll, or the version history of the CyAN processing.

**Not claimed:** that warming causes the bloom trends, any toxin or health meaning, or anything outside May–October.
