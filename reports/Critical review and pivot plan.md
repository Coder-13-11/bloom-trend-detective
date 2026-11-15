# Critical review and pivot plan (15 Nov 2026)

**Verdict.** The current submission is competent but not distinctive. Its trend tool repeats published work on a record too short to support trends, and the savings premise has no evidence behind it. The strongest direction is to stop asking "is there a trend?" and ask **"can the satellite trend be trusted?"**, by cross-examining it against independent field samples. I ran the first test of that today. It gives the project a real finding.

Evidence labels used below: **[Established]** = published or official source; **[Ours]** = computed in this repo; **[Hypothesis]** = not yet tested.

---

## 1. What we have, judged skeptically

| Asset | Verdict | Why |
|---|---|---|
| Reproducible pipeline, manifest with checksums, 31 tests, pre-registered protocols | **Valuable** | Rare in a hackathon, and it lets us run new tests fast and credibly. |
| EPA forecast vs last week's satellite view (6,980 lake-weeks) [Ours] | **Valuable but exposed** | The outcome labels and the persistence input come from the same satellite product. Simple baselines matching complex forecasts is known: Matthews 2022; Page et al. 2018. |
| 7-season CyAN trend picker [Ours] | **Weak** | Coffer et al. 2021 [Established] estimated that about a decade of imagery is needed before a trend outweighs variability. The CyAN team has already published national trend analyses (Schaeffer 2022; Mishra 2023). A Florida satellite map for 2002–2022 exists (FSU/FDEP report INV28). |
| MERRA-2 warming at every lake [Ours] | **True but generic** | 121 lakes share 26 grid cells. Any team can produce this from Giovanni or POWER in an hour. |
| "Simple logistic beats EPA" [Ours] | **Redundant for now** | Same label threat, and no confidence interval. |
| Dollar savings / restoration expenditure | **Unsupported** | The only costed Okeechobee intervention breaks even at p ≥ 0.91; the forecast never exceeded 0.23. No Florida action has a documented cost/loss ratio. |

**What is missing:** an independent source of truth. Every result so far is satellite checked against satellite.

## 2. What the literature says

**There is a live scientific dispute about satellite bloom trends.**
- Rising blooms from satellites: Ho et al. 2019 (*Nature*, Landsat); Wang et al. 2025 (MODIS, strongest in the subtropics after 2015) [Established].
- Challenged: Feng et al. 2020 called the Landsat trends unrealistic. Wilkinson et al. analysed field chlorophyll in 323 US lakes and found intensification in only 10.8% [Established].
- Within CyAN itself the picture is mixed. Schaeffer et al. 2022 found a strong national rise in bloom extent in 2017–2020 (OLCI era) but none in 2008–2011 (MERIS era). Mishra et al. 2023 found bloom magnitude fell in 25% of large lakes and rose in 4% between the two eras [Established].

**The instrument is a plausible suspect.** NASA reprocessed the OLCI ocean-colour products in 2022 and is preparing another update for recalibrated Level-1B data [Established]. The CyAN lake service reports no product version [Ours]. A step change in the record is therefore possible.

**Long harmonised records exist elsewhere.** Mishra et al. 2026 built a 25-year MERIS–MODIS–OLCI record for the Great Lakes with a deep-learning bridge [Established]. That is the frontier for trend work; we cannot reproduce it in a day.

**Novelty check on the proposed pivot.** I found no study testing whether CyAN's 2020–2026 trend in Florida agrees with field chlorophyll in the same lakes. NOAA assembled Florida field data for CyAN validation, but validation papers test retrievals, not trends. One round of searching is not proof of absence, so the claim should be "we found no prior test", never "first".

## 3. Past winners, briefly
Earth-science winners in 2023–2025 named a user and a place, shipped a live link, and reduced the answer to one number. No algal-bloom project has won a global award in 2021–2025; past bloom entries lacked measured accuracy and economics. Odds are long: 10 awards from 11,500+ submissions in 2025. What distinguishes a project at that level is one surprising, defensible finding, clearly told. Feature count doesn't.

## 4. New evidence from today [Ours]

Protocol Amendment 3 was written before any field value was analysed.

**Data.** Water Quality Portal (USGS/EPA), Florida lake chlorophyll-a corrected for pheophytin.
- 146,396 Florida lake records for 2000–2026; 141,907 usable after cleaning. Of these, 26,629 fall inside our lakes, and 5,812 are in the 2020–2025 warm seasons used for the primary test.
- Sources: Florida LAKEWATCH, FDEP, counties and water management districts.
- 2,993 stations fall inside 115 of our 121 lakes.

**Primary result, 2020–2025, 45 lakes with good coverage in both records:**

| Question | Result |
|---|---|
| Does field chlorophyll rise? | Median **+7.5% per year** (95% CI 2.6 to 13.2); 33 lakes up, 12 down |
| Satellite bloom extent, same lakes | Median +0.35 points per year (CI 0.09 to 1.77) |
| Do lakes that rise by satellite also rise in the field? | Not shown: ρ = 0.12 (CI −0.17 to 0.39) |
| Does the satellite track the field year to year? | Yes, modestly: median within-lake ρ = 0.30 (CI 0.26 to 0.49); positive in 81% of lakes |
| Pre-registered verdict | **Corroborated** |

**The shape differs, and that is the interesting part** (29 lakes with all six years in both records; exploratory):

| Year | Field chlorophyll, geometric mean (µg/L) | Satellite bloom-week share |
|---|---|---|
| 2020 | 8.9 | 0.17 |
| 2021 | 8.4 | 0.16 |
| 2022 | 12.7 | 0.19 |
| 2023 | 13.3 | 0.25 |
| 2024 | 11.6 | 0.25 |
| 2025 | 10.1 | 0.31 |

Field chlorophyll stepped up in 2022–2023 and then eased. The satellite signal kept climbing. So the rise from 2020–21 to 2022–23 looks real, and the continued climb in 2024–2025 is not confirmed by field data.

**Caveats.**
- Lakes share weather, so the intervals are too narrow.
- 2025 field data may be incomplete because of reporting lag: 6.9 sampling dates per lake against about 10 in 2022–2024.
- Field samples measure total chlorophyll at points; the satellite measures a cyanobacteria-related signal over the surface.
- With 2026 included, the field CI crosses zero (−0.8 to 10.6, 30 lakes), but 2026 field data are about 30% complete.

**A second test is feasible.** 506 lake-weeks across 86 lakes have the EPA forecast, last week's satellite state and a field sample in the same week. That is independent ground truth for the forecast comparison, which would remove our biggest threat.

## 5. Competing directions

| | Direction | Novelty | Validity | On-challenge | Feasible today | Verdict |
|---|---|---|---|---|---|---|
| A | Keep the trend picker as is | Low: published by the CyAN team; Giovanni-like | Weak: 7 seasons | Yes | Done | Baseline only |
| **B** | **Second opinion: cross-examine the satellite trend with field data, and score the forecast against field truth** | Moderate to good: engages a published dispute; no prior test found | Strong: independent data, pre-registered | Yes: trend + significance, plus "is it significant *and real*?" | Yes: first test done | **Strongest** |
| C | Build a better forecaster (add recent bloom state) | Low: Matthews 2022 | Label threat unless scored on field truth | No | Partly | Fold into B's decision test only |
| D | Savings / restoration-cost tool | — | Unsupported; would require invented costs | No | No | **Drop** |
| E | 20-year multi-sensor record, or PACE hyperspectral | High, but done for the Great Lakes (Mishra 2026) | Strong if done properly | Yes | No: needs Earthdata login, days of work | Name as future work |
| F | Where to send sampling crews | Moderate | Good if scored on field truth | Indirect | Yes, as part of B | Becomes B's "so what" |

**Why B.**
- It turns our weakest point (satellite checked against satellite) into the contribution.
- It answers the challenge more deeply than a significance test does: a trend can be statistically significant and still be an artifact.
- It is useful to real people: the CyAN team at EPA and NASA, and Florida agencies that rely on satellite indicators.
- It needs no assumptions about intervention costs.
- Either outcome of each test is publishable, so there is no incentive to tilt results.

**What B is not.** It is not a savings estimate, a toxin or health tool, or proof of what causes the rise. The honest impact claim is narrower: *before money or alarm follows a satellite trend, check it against the field record; here is a public tool and a first result.*

## 6. Roadmap for direction B

**Experiments**

| # | Experiment | Status | Method | Output |
|---|---|---|---|---|
| E1 | Do field data confirm the satellite trend? | **Done** | Amendment 3 | `outputs/insitu_v1/` |
| E2 | Has the satellite–field relationship drifted? This is the direct instrument test. | To run (about 1 h) | Same-week matchups, 2020–2025. Model the satellite bloom state on field chlorophyll plus a year effect, clustered by lake. Year effects near zero mean no drift. | Year-effect chart with CIs |
| E3 | Which signal better predicts what a field crew finds? | To run (about 1 h) | 506 lake-weeks. Outcome: field chlorophyll ≥ 12 µg/L. Compare the EPA forecast, last week's satellite view and the seasonal average. Brier, ROC-AUC, PR-AUC, relative economic value, lake-clustered bootstrap. | Table and one chart |
| E4 | Long-record field trends, 2000–2025, per lake | **Done** | Mann-Kendall, Sen's slope, many-lake correction | Only 13 lakes have ≥ 15 well-sampled seasons. None shows a significant trend; the median is −1.0% per year. So the recent rise is not a long-term trend in those lakes. |

E2 and E3 get a written protocol (Amendment 4) before they are run.

**Product changes**
- The lake page shows satellite and field series side by side, with an agreement verdict: "both rising", "satellite only", "field only" or "neither".
- A statewide "cross-examination" page presents E1 and E2 as the detective's case: suspects (real greening, instrument drift, sampling changes), evidence, verdict.
- The decision page reports E3 in place of the satellite-labelled comparison if E3 is conclusive; otherwise it shows both with the caveat.
- MERRA-2 stays as context, demoted from headline.

**Deliverables**
- Rebuilt site, 7 slides and project-page text around one sentence:
  *"Satellites say Florida's lakes are getting greener. We checked against 26,629 field samples in 115 lakes: the rise is real through 2023, and the satellite's continued climb since then is not yet confirmed."* The final wording depends on E2.
- NASA data list: the CyAN index archived at NASA OB.DAAC, MERRA-2 via NASA POWER, MODIS imagery. Partner and other data: ESA Sentinel-3, and the Water Quality Portal (USGS/EPA).

**Suggested order for today:**
1. Amendment 4 and E2 + E3 (2 h).
2. Site rebuild (3 h).
3. Slides and page text (1.5 h).
4. Hosting and submission by early evening, leaving a buffer.

**Risks**
- E2 may be inconclusive; we would say so.
- Field-data reporting lag could bias 2025. The balanced-panel and sampling-count checks stay visible.
- Station matching uses lake outlines with a 150 m tolerance; a few stations may be in canals or marinas.
- Eligibility items remain yours: the provenance statement, the AI-idea statement and team size.

## 7. Claims to retire
- "Could reduce restoration expenditure" — no evidence.
- "Simple model beats EPA's forecast" as a headline — only as a field-scored result, if E3 supports it.
- "Bloom season is getting worse" stated flat — replace with the cross-examined version.
- "First" anything.

## 8. Update after the pivot (same day)
Protocol Amendment 4 was written before either test ran.

- **E2, drift test.** For the same field chlorophyll, lake and month, the satellite reads higher each year: +2.5 points of bloom extent per year (95% CI 1.4 to 3.6; 2,541 same-week matchups, 106 lakes). By 2025 the gap is +12 points against 2020 (CI 6.5 to 17.8). Both sensitivities agree. This does not prove instrument drift: a real shift toward cyanobacteria at the same total chlorophyll, or a change in sampling, would look the same.
- **E3, field-truth forecast test.** Against field chlorophyll ≥ 12 µg/L (506 lake-weeks, 86 lakes), ROC-AUC is 0.759 for the EPA forecast and 0.752 for last week's satellite extent. The difference is +0.007 (CI −0.039 to 0.050), so no difference is shown. The logistic baseline (0.763) and the seasonal average (0.745) are in the same range. The earlier satellite-graded advantage of "last week's view" does not hold against independent data.
- **Correction.** The sentence in section 6 originally said "140,000 field samples". That was the statewide total. The number actually used is 26,629.
