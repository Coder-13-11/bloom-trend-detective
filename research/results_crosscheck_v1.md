# Results: field cross-check v1 (protocol Amendments 3 and 4), generated 2026-11-15

Code: `src/bloom/insitu.py`, `src/bloom/fieldtruth.py`. Outputs: `outputs/insitu_v1/`, `outputs/fieldtruth_v1/`.
Reproduce from cached data:
```
PYTHONPATH=src python -m bloom.insitu       # about 1 min
PYTHONPATH=src python -m bloom.fieldtruth   # about 12 min (bootstrap)
```

## Data
- Water Quality Portal, Florida lakes, "Chlorophyll a, corrected for pheophytin", 2000–2026: 146,396 rows; 141,907 usable.
- 2,993 stations fall inside 115 of the 121 lakes (2,918 inside the outline, 75 within 150 m).
- 26,629 records are in those lakes; 5,812 of them are in May–October of 2020–2025.

## Amendment 3 — do field samples confirm the satellite trend? (confirmatory)
Window 2020–2025; 45 lakes with ≥ 5 of 6 valid seasons in both records.

| Statistic | Result |
|---|---|
| P1 field: median Sen slope of seasonal median chl-a | **+7.5% per year [2.6, 13.2]**; 33 lakes up, 12 down |
| P1 satellite extent, same lakes | +0.35 points per year [0.09, 1.77]; 32 up, 4 down, 9 zero |
| P2 Spearman of satellite vs field slopes across lakes | 0.12 [−0.17, 0.39] |
| P3 within-lake year-to-year Spearman | median 0.30 [0.26, 0.49]; positive in 81% of 42 lakes |
| Verdict by the pre-set rule | **Corroborated** |

Sensitivity with 2026 (field data about 30% complete): 30 lakes; field +5.5% per year [−0.8, 10.6]. By the rule this reads "not corroborated", but the window is unreliable.

**Exploratory, balanced panel** (29 lakes with all six seasons in both records):

| Year | Field geometric mean chl-a (µg/L) | Satellite bloom-week share |
|---|---|---|
| 2020 | 8.9 | 0.166 |
| 2021 | 8.4 | 0.162 |
| 2022 | 12.7 | 0.192 |
| 2023 | 13.3 | 0.252 |
| 2024 | 11.6 | 0.250 |
| 2025 | 10.1 | 0.306 |

Field chlorophyll stepped up in 2022–23 and then eased; the satellite kept rising. 2025 has fewer field dates per lake (6.9 against about 10), which suggests reporting lag.

**Long field record (descriptive).**
- 65 lakes have ≥ 6 well-sampled seasons in 2000–2025; none is significant after BH.
- 13 lakes have ≥ 15 seasons; none is significant; the median is −1.0% per year.

## Amendment 4, E2 — has the satellite–field relationship drifted? (confirmatory)
2,541 same-week matchups, 106 lakes, 2020–2025, May–October.
Model: satellite bloom extent (points) ~ log10 field chl-a + lake FE + month FE + year.

| | Year slope (points per year) | 95% CI |
|---|---|---|
| Primary (extent) | **+2.46** | [1.40, 3.62] |
| Sensitivity: lakes with matchups in ≥ 5 of 6 years (88 lakes) | +2.47 | [1.39, 3.68] |
| Sensitivity: outcome = lake-median DN | +4.92 DN per year | [3.08, 6.85] |

Year effects against 2020:

| 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| −0.2 [−3.9, 3.0] | +4.9 [1.4, 8.8] | +7.2 [2.4, 12.4] | +8.2 [3.6, 13.3] | +12.0 [6.5, 17.8] |

The log10 chl-a coefficient is 16.3 [12.0, 20.8].

**Verdict by the pre-set rule:** the satellite reads higher for the same field chlorophyll in later years.

**What this does and does not show.**
- It is consistent with instrument or processing drift.
- It is equally consistent with a real shift toward cyanobacteria at the same total chlorophyll, or with changes in where and when samples are taken.
- Noise in the field measurements biases the chlorophyll coefficient toward zero. That can inflate the year effect. Its size is therefore an upper-leaning estimate.

## Amendment 4, E3 — which signal better predicts what a field crew finds? (confirmatory)
506 forecast windows (2025: 411; 2026: 95), 86 lakes. Outcome: field chl-a ≥ 12 µg/L (base rate 0.457).

| Signal | ROC-AUC | PR-AUC |
|---|---|---|
| EPA forecast probability | 0.759 | 0.718 |
| Last week's satellite extent | 0.752 | 0.655 |
| Last week's satellite bloom state (binary) | 0.689 | 0.611 |
| Same-week satellite bloom state (reference) | 0.686 | 0.606 |
| Seasonal average (secondary) | 0.745 | 0.746 |
| Logistic on last week's satellite state (secondary) | 0.763 | 0.686 |

- **Primary:** AUC(EPA) − AUC(last week's extent) = **+0.007 [−0.039, 0.050]**. No difference shown.
- Secondary: logistic − EPA = +0.003 [−0.039, 0.053].
- Sensitivity at ≥ 20 µg/L: EPA 0.822, last week's extent 0.810; difference +0.012 [−0.036, 0.056].

**Consequence for results_v1.** The satellite-graded advantage of persistence and of the logistic baseline over the EPA forecast is not reproduced against field data. Limitation 12 (shared-sensor autocorrelation favours persistence) is the likely reason. The results_v1 numbers stand as computed, but they should be described as satellite-graded.

## Not claimed
Toxins or health; dollar savings; the cause of the drift signature; anything outside Florida's matched lakes.
