# Protocol — BloomEconomics Arm A, v1 (prespecified 2026-11-14)

Written **before** running the Florida multi-lake evaluation (`config/experiment.yaml`).
Disclosure: before writing this, I had already inspected the Lake Okeechobee-only join of
EPA forecasts to CyAN labels (68 weeks, 2 bloom weeks). No Florida-wide result had been seen.

## Research question (revised from the master plan after Phase 0)

**RQ.** For the operational EPA weekly cyanoHAB forecast as archived for 2025–2026, over
Florida's satellite-resolvable lakes: across the range of cost/loss ratios at which a manager
might act, does acting on the forecast reduce expected expense relative to (a) climatology
and (b) simply acting on last week's satellite observation (persistence) — and does the
answer differ for *bloom onsets* (non-bloom → bloom), which persistence cannot anticipate?

**Why this, not the original savings question.** Phase 0 showed (i) the only documented,
costed Okeechobee intervention (USGS SIR 2024-5091 HABITATS) has break-even probability
≥ 0.91 in every scenario, while the EPA forecast for Okeechobee never exceeded 0.23, so
estimating dollar savings from that action is not supported; (ii) no Florida agency action
with documented cost, latency and efficacy at forecast scale was found. The cost-loss
framework lets value be stated *conditionally on* the cost/loss ratio α = C/(eL) without
assuming any particular intervention's efficacy. A dollar figure requires α, which requires
evidence that does not yet exist here.

## Hypotheses (mapped to master plan)
- **H0 (primary):** For α in [0.05, 0.5], REV(EPA forecast) − REV(persistence) ≤ 0 on held-out 2025–26 lake-weeks.
- **H1:** There is a contiguous α range where the difference is > 0 with a lake-clustered 95% bootstrap interval excluding 0.
- **H2 (timing):** The forecast's advantage over persistence is larger on onset-eligible weeks than on all weeks.

## Data
- Forecasts: EPA Qlik table `AllWeeks_CyanForecasts` (148,988 rows, 2025–2026, 2,191 lakes), exported via the Qlik Engine API (`scripts/qlik_export.py`). Issue/availability timestamps are **not** in the archive.
- Outcomes: CyAN weekly composite DN histograms (cyan.epa.gov waterbody API), label = median DN over valid pixels ≥ 130 (EPA code `cyan_processing_conus.R` L170). Pixel set differs from EPA's (see limitations).
- Lakes: 121 of 132 Florida forecast lakes matched by name + centroid distance (`data/interim/fl_lake_map.csv`); 11 excluded with recorded reasons.

## Design
- Unit: lake-week (Sunday–Saturday). Outcome week W. Persistence uses observed week W−1 (sensitivity: W−2).
- Eligible set (identical for all policies): outcome known, W−1 state known, forecast present. Weeks with < 50% valid water pixels are `unknown` (never negative). Counts of each exclusion reported.
- Onset subset: eligible weeks with W−1 = non_bloom.
- Baselines: climatology (lake × month, 2020–2023, Beta-shrunk to all-lake month rate, k = 5); persistence (binary); logistic regression on W−1 median DN, W−1 fraction ≥ DN130, W−1 bloom, seasonal harmonics (fit 2020–2023 only).
- Test years: 2025 and 2026 (all available forecasts). 2024 reserved; no thresholds tuned on test. Decision rule for probabilistic forecasts: act iff p > α (rational for calibrated p; prespecified, not optimised).
- Metrics: Brier, log loss, ROC-AUC, PR-AUC, reliability table; REV curve (Richardson 2000) over α grid; lake-clustered paired bootstrap (1,000 reps, seed 20261114) of REV(EPA) − REV(persistence) at α ∈ {0.05, 0.1, 0.2, 0.3, 0.5}.
- Reporting: all policies on the same windows; per-year and pooled; null results reported.

## What would NOT be claimed regardless of result
Toxicity or health validity; avoided damages; agency or taxpayer savings; skill outside Florida
resolvable lakes; issued-as-of skill (issue times unknown); causal effect of any intervention.

## Amendment 1 (2026-11-14, before any Florida-wide result was viewed)
CyAN API throughput (~1 lake-year per 15–60 s) makes the full 2020–2026 pull for 121 lakes take
several hours. Changes: (a) download order is 2025, 2026, then training years newest-first;
(b) the **primary** analysis (EPA vs persistence, lag-1 and lag-2) needs no training data and is
run on 2025–26 alone; (c) climatology and logistic baselines are **secondary**, evaluated on
their own common window set once ≥ 10 training bloom weeks exist; training years actually
used are recorded in `run_manifest.json`. Lag-2 persistence with an unknown W−2 state = no action.

## Amendment 2 — Trend analysis for NASA Space Apps "Be An Earth System Trend Detective!" (2026-11-15, written BEFORE any trend was computed)
**Purpose.** Answer the challenge's question: for a chosen Florida lake and Earth variable, is there a trend over time, how large, and is it significant? Descriptive only: no causal links between variables.

**Disclosure.** Looked at beforehand:
- Okeechobee's yearly bloom-week counts (`outputs/report/okeechobee_by_year.csv`).
- Data coverage checks: CyAN covers weekly composites through 2026-11-01 for all 121 lakes.

Not looked at before writing this: no multi-lake trend, and no NASA POWER values.

**Variables**
- **V1 (primary): bloom-week share.** For each lake-year, bloom weeks ÷ known weeks over the May–October season.
  - The season counts weeks whose start date falls in May–October.
  - "Known" means valid_fraction ≥ 0.5 and label bloom or non_bloom, the same rule as D-014.
  - A lake-year counts only if it has ≥ 13 known weeks.
  - A lake is tested only if ≥ 6 of its 7 seasons (2020–2026) count.
- **V2 (secondary): bloom extent.** For each lake-year, the mean over May–October weeks with valid_fraction ≥ 0.5 of the fraction of valid pixels with DN ≥ 130. The same inclusion rules apply.
- **V3: NASA MERRA-2 warm-season temperature and rainfall.**
  - Source is NASA POWER (monthly point API, parameters T2M and PRECTOTCORR) at each lake centroid, 1981–2025.
  - Temperature: mean of the May–October monthly T2M.
  - Rainfall: May–October total, computed as the monthly mean rate × days in the month, if POWER reports a daily-rate unit.
  - 2026 is excluded because its year is incomplete.

**Tests**
- Mann-Kendall, two-sided, α = 0.05, with Sen's slope as the trend size.
- p-value: exact permutation p for n ≤ 8, which handles ties. Otherwise the normal approximation with tie correction.
- Sen-slope 95% CI by the Gilbert (1987) rank method.
- V1 and V2: Benjamini–Hochberg FDR at q = 0.05 across tested lakes, separately per variable. V1 is the confirmatory family.
- V3: no FDR across lakes, because many lakes share one MERRA-2 grid cell and so are not independent. Results are reported per lake as "the regional air at this lake's grid cell", and the number of distinct POWER grid values is reported.
- V3 also reports the lag-1 autocorrelation of the residuals from Sen's line. It is flagged if |r1| > 2/√n, because plain MK p-values may then be too small.
- Linear trend only. No removal of the seasonal cycle, because annual season aggregation is used instead.

**Verdict wording**
| Condition | Wording |
|---|---|
| Adjusted p < 0.05 | "Significant upward/downward trend" |
| Raw p < 0.05 but adjusted p ≥ 0.05 | "Possible trend — not significant after accounting for testing many lakes" |
| Otherwise | "No clear trend yet (n = k seasons)" |

For V3 the adjusted p is the raw p.

**Expected power.** With 7 seasons, the smallest exact two-sided p is 2/5040 ≈ 0.0004, and only a perfectly monotonic series reaches it. Null results are expected and will be reported as findings.

**Not claimed.** That temperature or rainfall trends cause bloom trends. Toxin or health relevance. Trends outside May–October or beyond the record.

Code: `src/bloom/trends.py`, `src/bloom/power.py`; config `config/trends.yaml`; output `outputs/trends_v1/`.

## Amendment 3 — Do field samples confirm the satellite trend? (2026-11-15, written BEFORE any field chlorophyll value was analysed)
**Why.** Amendment 2 found a coherent statewide rise in the CyAN bloom signal (exploratory). Published work disagrees on whether satellite bloom trends are real:
- Ho et al. 2019 and Wang et al. 2025 report rising blooms from satellites.
- Feng et al. 2020 and Wilkinson et al. 2022 dispute this; Wilkinson et al. use in-situ data.
- Mishra et al. 2023 report no increase in large US lakes from MERIS to OLCI.

NASA reprocessed OLCI in 2022, and the CyAN API reports no product version. An independent check is needed.

**Disclosure.** Seen before writing this:
- Record counts per year in the Water Quality Portal: about 10–13k Florida lake results per year for 2020–2025, and 3,682 for 2026.
- Column headers and one data row.
- The satellite results of Amendment 2.

No field value has been aggregated or plotted.

**Field data.**
- Source: Water Quality Portal (USGS/EPA), Florida, site type "Lake, Reservoir, Impoundment".
- Characteristic: "Chlorophyll a, corrected for pheophytin".
- Organizations: all, including Florida LAKEWATCH, FDEP and the counties.
- Raw files: `data/raw/D10_wqp/`.

**Matching.** A station belongs to a lake if its coordinates fall inside the lake's NHD polygon (CyAN geometry service, `data/raw/D11_lake_geom/`) or within 150 m of the polygon boundary. Stations that match two lakes are dropped.

**Cleaning.**
- Units are converted to µg/L: mg/m3 = µg/L, mg/L × 1000, ppb = µg/L.
- Dropped and counted: non-numeric values, non-detects without a value, and values ≤ 0.
- Values are otherwise used as reported (no detection-limit substitution).

**Aggregation.** May–October only.
- Per lake and sampling date: the mean across stations.
- Per lake-year: the median across dates of log10(chl-a), and separately the share of dates with chl-a ≥ 12 µg/L. That is the same threshold the satellite bloom label approximates.
- A lake-year counts with ≥ 3 sampling dates.

**Comparison window.** 2020–2025.
- 2026 is excluded from the primary analysis because its field data are incomplete: about 30% of the usual record count, a reporting lag.
- Satellite slopes are recomputed on 2020–2025 for the same lakes.
- 2026 is shown only as a sensitivity.

**Lakes.** Those with ≥ 5 of 6 valid seasons in BOTH the field and the satellite series.

**Primary questions and statistics**
- **P1. Does field chlorophyll rise?**
  - Statistic: the median across lakes of the per-lake Sen slope of the seasonal median log10 chl-a (reported as % per year).
  - 95% CI from a lake bootstrap (2,000 resamples, seed 20261115).
  - The same statistic is computed for satellite bloom extent (V2) on the same lakes and years.
- **P2. Do lakes that rise by satellite also rise in the field?** Spearman correlation across lakes between the satellite V2 slope and the field slope, with a bootstrap CI.
- **P3. Does the satellite track the field year to year?** Per lake, the Spearman correlation between yearly satellite V2 and the yearly field median (6 points). Reported as the median across lakes and the share of lakes with positive correlation.

**Reading the result (fixed in advance)**
- **Corroborated:** the P1 field CI is above 0, and P2 or P3 is positive.
- **Not corroborated:** the P1 field CI includes 0 or lies below it while the satellite CI is above 0.
- **Inconclusive:** fewer than 20 lakes qualify.

Lakes share weather, so the bootstrap CIs are too narrow. This is stated wherever a result is shown.

**Secondary (descriptive).**
- The statewide share of field sampling dates ≥ 12 µg/L by year, alongside the satellite bloom-week share.
- Long-record field trends, 2000–2025, per lake: Mann-Kendall and Sen's slope, with BH correction across lakes.
- Years needed to confirm each satellite trend, using Weatherhead et al. (1998): n* = [3.3·σ/|ω| · sqrt((1+φ)/(1−φ))]^(2/3).

**Not claimed.**
- That field chlorophyll and the satellite index measure the same thing. One is total chlorophyll at sampling points; the other is cyanobacteria-related signal over the lake surface.
- Any causal attribution.
- Anything about toxins.

Code: `src/bloom/insitu.py`. Output: `outputs/insitu_v1/`.

## Amendment 4 — Instrument-drift test and field-truth forecast test (2026-11-15, written BEFORE either was computed)
**Disclosure.** Seen before writing:
- The Amendment 3 results, including the exploratory year table in which field chlorophyll eased after 2023 while the satellite kept rising.
- The count of forecast lake-weeks that also have a field sample: 506, across 86 lakes.

No matchup regression and no field-scored forecast metric has been computed.

### E2. Has the satellite–field relationship drifted?
**Matchups.** Lake-weeks in 2020–2025, May–October, where:
- the CyAN weekly composite has valid_fraction ≥ 0.5, and
- at least one field sample was taken in the same Sunday–Saturday week.

The field value is log10 of the mean of the week's lake-date means.

**Primary model.** Ordinary least squares:
satellite bloom extent (share of valid pixels with DN ≥ 130) ~ log10(field chl-a) + lake fixed effects + month fixed effects + year (linear).

**Primary statistic.** The year coefficient, in points of extent per year at fixed field chlorophyll. 95% CI from a lake-cluster bootstrap (2,000 resamples, seed 20261115).

**For display.** The same model with year fixed effects (2020 as reference) in place of the linear year.

**Sensitivity.** Outcome = lake-median DN. Lakes limited to those with matchups in ≥ 5 of the 6 years.

**Reading (fixed in advance).**
- CI above 0: "the satellite reads higher for the same field chlorophyll in later years". This is consistent with instrument or processing drift. It is equally consistent with a real shift toward cyanobacteria at the same total chlorophyll, or with changes in where and when samples are taken. The test cannot separate these.
- CI includes 0: "no drift shown".

### E3. Which signal better predicts what a field crew finds?
**Windows.** The eligible 2025–26 forecast windows of the primary analysis (forecast present, satellite outcome known, last week's satellite state known) that also have ≥ 1 field sample in the outcome week.

**Outcome.** Field chl-a ≥ 12 µg/L, using the week's mean of lake-date means. Sensitivity threshold: ≥ 20 µg/L.

**Signals compared**
- EPA forecast probability.
- Last week's satellite bloom extent (continuous).
- Last week's satellite bloom state (binary persistence).
- Secondary: the prespecified climatology and logistic baseline from `outputs/fl_v1/`, on the subset where they exist.
- Reference, not a forecast: the same-week satellite bloom state. It shows how well the satellite label itself matches the field.

**Primary statistic.** ROC-AUC(EPA probability) − ROC-AUC(last week's satellite extent). 95% CI from a lake-cluster bootstrap (2,000 resamples).

**Also reported.** PR-AUC and the base rate.

**Not primary: Brier score and relative economic value.** Total chlorophyll ≥ 12 µg/L is much more common than the satellite bloom label, so neither signal is calibrated to this outcome.

**Reading (fixed in advance).**
- CI above 0: the forecast ranks field outcomes better.
- CI below 0: last week's satellite view ranks better.
- CI includes 0: no difference shown.
- Fewer than 150 windows or fewer than 30 events or non-events: inconclusive.

**Caveats (stated in advance)**
- Field sampling is not random in space or time.
- Total chlorophyll is not cyanobacterial chlorophyll.
- A point sample is not a lake median.
- 2026 field data are incomplete.

Code: `src/bloom/fieldtruth.py`. Output: `outputs/fieldtruth_v1/`.
