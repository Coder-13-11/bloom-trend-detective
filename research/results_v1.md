# Results v1 — Florida, 2025–2026 (generated 2026-11-14)

> **Read with `results_crosscheck_v1.md`.** Everything below is graded against satellite labels. Against independent field samples (Amendment 4, E3) the EPA forecast and last week's satellite view show no difference in ranking skill, so the advantages reported here for persistence and the logistic baseline should not be read as real-world advantages.

Data mode: **REAL** (EPA archived weekly forecasts exported from the dashboard + CyAN API weekly composites).
Outcome = CyAN lake-median DN ≥ 130 (satellite chlorophyll proxy, not toxins). Forecast issue times unknown.
Files: `outputs/fl_v1_primary/` (confirmatory), `outputs/fl_v1_exploratory/` (post hoc).

## Evaluation set
8,228 Florida forecast lake-weeks → 6,980 eligible (120 lakes, 1,974 bloom weeks).
Excluded: 462 no CyAN week, 294 outcome unknown (< 50% valid pixels), 492 previous week unknown.
Onset-eligible (previous week non-bloom): 5,007 windows, 152 onsets. New-episode onsets
(4 previous observed weeks all non-bloom, exploratory): 3,738 windows, 65 onsets.

## Primary (prespecified) — EPA forecast vs persistence of last week's observation
| | Brier | ROC-AUC | PR-AUC | mean p / base rate |
|---|---|---|---|---|
| All weeks, EPA | 0.099 | 0.928 | 0.843 | 0.280 / 0.283 |
| All weeks, persistence | **0.043** | 0.946 | 0.874 | — |
| Onset weeks, EPA | 0.064 | 0.850 | 0.189 | 0.115 / 0.030 |
| Onset weeks, persistence | 0.030 | 0.500 | 0.030 | — |
Both years separately give the same ordering (2025 and 2026 Brier: EPA 0.099/0.099, persistence 0.046/0.040).

Relative economic value difference REV(EPA) − REV(persistence), lake-clustered 95% bootstrap:
| α = C/(eL) | all weeks | onset weeks |
|---|---|---|
| 0.05 | −0.05 [−0.28, 0.14] | **+0.32 [0.12, 0.48]** |
| 0.10 | **−0.22 [−0.37, −0.10]** | −0.04 [−0.33, 0.18] |
| 0.20 | **−0.22 [−0.32, −0.14]** | **−0.60 [−1.02, −0.25]** |
| 0.30 | **−0.21 [−0.30, −0.14]** | **−0.99 [−1.53, −0.53]** |
| 0.50 | **−0.33 [−0.46, −0.23]** | **−1.86 [−2.84, −1.09]** |

**H0 (no advantage over persistence, α ∈ [0.05, 0.5]) is not rejected for all weeks;** persistence is
significantly better for α ≥ 0.1. **H1 holds only in a narrow band:** on onset weeks at α = 0.05.
**H2 is supported in direction:** the forecast's relative value is concentrated on onsets and on cheap actions.
At α ≥ 0.1 acting on the forecast for onset weeks is worse than never acting (negative REV), because
probabilities are inflated on non-bloom lakes (mean p 0.115 vs 3.0% onset rate).

Calibration (all weeks): low bins under-forecast (p≈0.07 → 14% observed), top bin over-forecast (p≈0.90 → 83%).

## Lag-2 sensitivity (persistence that only knows the week before last)
If last week's composite is not yet available at decision time, persistence weakens: on all weeks
REV at α = 0.1 is EPA 0.47 vs lag-2 0.40; at α = 0.2, 0.62 vs 0.71. The crossover moves from
α ≈ 0.05 to ≈ 0.15. **Observation latency therefore determines which information source is worth
more** — exactly the "realizable lead time" variable in H2, and it is unmeasured (D-004).

## Exploratory (post hoc — needs an untouched season to confirm)
- **E1 new-episode onsets** (65 events): EPA beats never-acting only for α ≤ 0.03
  (α = 0.03: +0.24 [0.02, 0.41]); for α ≥ 0.075 it is significantly worse than never acting.
  Many "onsets" in the primary analysis are threshold flicker after a one-week dip.
- **E2 hybrid rule** (act if last week bloomed OR EPA p > α): beats persistence for α ≤ 0.05
  (α = 0.05: +0.19 [0.06, 0.34]), no difference at 0.075–0.1, slightly worse at α ≥ 0.15.

## Interpretation of the primary block (claim strength: descriptive, one state, two seasons, satellite labels)
For Florida's resolvable lakes, the EPA weekly forecast adds decision value over simply acting on
the latest satellite observation **only for actions that cost less than roughly 3–5% of the loss
they would avoid**, and mainly by flagging lakes that are not yet blooming. That profile fits the
use EPA itself recommends (informing monitoring) and does not fit expensive mitigation: the only
costed Okeechobee mitigation (USGS HABITATS) sits at α ≥ 0.9.

**Not shown:** that any real Florida action has α ≤ 0.05 (cost and avoidable loss of confirmatory
sampling are undocumented here); any dollar saving; toxin or health relevance; skill with true
issue-time information.


## Secondary baselines (prespecified; trained 2020–2023, 22,881 lake-weeks; tested 2025–26)
Same 6,980 windows. `outputs/fl_v1/`.
| | Brier all | ROC-AUC all | PR-AUC all | Brier onset | PR-AUC onset |
|---|---|---|---|---|---|
| EPA forecast | 0.099 | 0.928 | 0.843 | 0.064 | 0.189 |
| Climatology (lake × month) | 0.125 | 0.911 | 0.848 | 0.030 | 0.173 |
| Persistence (lag 1) | 0.043 | 0.946 | 0.874 | 0.030 | 0.030 |
| **Logistic (last week's satellite state + season)** | **0.034** | **0.988** | **0.971** | **0.024** | **0.330** |

The logistic baseline has higher REV than the EPA forecast at every α in the grid, on all weeks and on onsets
(e.g. α = 0.1: 0.82 vs 0.47 all weeks; 0.44 vs −0.04 onsets). On onsets the EPA forecast's Brier score is worse
than climatology's (0.064 vs 0.030) because of inflated probabilities on non-blooming lakes.

**Latency check (exploratory):** refitting the logistic on information two weeks old (W−2 only, 2020–23 fit)
still beats the EPA forecast: REV difference α = 0.1: +0.26 [0.14, 0.42] all weeks, +0.44 [0.26, 0.68] onsets;
CIs exclude 0 for every α from 0.05 to 0.5 (`outputs/fl_v1_exploratory/logit_lag2_vs_epa.csv`).

### Revised interpretation
For deciding *which Florida lake-weeks will exceed the EPA satellite bloom threshold*, a five-feature logistic
model on recent CyAN observations dominates the operational EPA forecast across all cost/loss ratios tested,
even with two weeks of data latency. The EPA model's design omits recent bloom state (conus_inla.R L199);
adding it is the obvious, testable improvement. This is an **empirical observation about one region and
two seasons**, not a claim that the national model is poorly built — it targets 2,192 lakes nationally.

**Biggest threat to this conclusion:** our outcome labels are computed from the CyAN API histogram, which
is also where the logistic's features come from; the EPA forecast targets EPA's own label (different pixel
mask, possibly different product version). Any label mismatch penalises EPA and favours models fitted to
our labels. Resolving this needs EPA's own weekly labels (request from EPA) or field-validated outcomes.

## Next decisive measurements
1. Document α for FDEP/SFWMD satellite-triggered sampling (cost per trip; what earlier detection avoids).
2. Measure CyAN weekly-composite publication latency, to choose lag-1 vs lag-2 as the realistic comparator.
3. Pre-register E2 (hybrid) and the new-episode endpoint; test on the 2027 season.
4. Field validation of onsets against FDEP microcystin samples (D04).
5. Obtain EPA's own weekly CyAN labels to rule out label-definition mismatch (the main threat above). Request drafted: `docs/epa_data_request_draft.md` (not sent).
6. Test the logistic baseline nationally (2,191 lakes) and on 2027 as an untouched season.
