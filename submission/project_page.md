# Space Apps 2026 project page: text to paste

Challenge: **Be An Earth System Trend Detective!** Deadline: **Sun 15 Nov 2026, 11:59 p.m. local event time.**

Before pasting:
- Replace every `[BRACKET]`.
- Make sure every link opens without a login.
- Demo = the slides PDF link below: exactly 7 slides, including the title.

---

## Project Name
Bloom Trend Detective: Florida Lakes

## High-Level Summary
Satellites say Florida's lakes are getting greener. Bloom Trend Detective asks whether that trend can be trusted, by cross-examining the satellite record against independent field water samples, lake by lake.

**The tool.** Pick a Florida lake and a variable, and get a time series, a rate of change, a significance test and a plain-language verdict. The variables are the satellite cyanobacteria index (CyAN, archived by NASA), field chlorophyll, and NASA MERRA-2 air temperature and rainfall. Each lake also gets a "second opinion": does the field record agree with the satellite?

**What we found.** All test rules were written down before the results were computed.
- **The satellite says rising.** The share of warm-season weeks flagged as blooming rose from 11% in 2020 to 30% in 2026, averaged over lakes.
- **Field samples agree on direction.** Field chlorophyll rose a median 7.5% per year over 2020–2025 (95% CI 2.6 to 13.2; 45 lakes).
- **But the satellite reads higher every year for the same field chlorophyll:** +2.5 points of bloom extent per year (95% CI 1.4 to 3.6; 2,541 same-week matchups). Field chlorophyll eased after 2023 while the satellite kept climbing.
- **Verdict.** The rise through 2023 looks real. The climb since then is not confirmed. It could be instrument drift, a real shift toward cyanobacteria, or a change in sampling.

**Decision test.** We also asked whether EPA's weekly bloom forecast beats simply looking at last week's satellite view.
- Graded against satellite labels, last week's view looked clearly better.
- Graded against field samples, there was no clear winner.
- That corrected our own first result. Field truth is the fairer judge.

## Demo
https://coder-13-11.github.io/bloom-trend-detective/BloomTrendDetective_slides.pdf (7 slides)

## Final Project
Live tool: https://coder-13-11.github.io/bloom-trend-detective/
Code, data manifest and tests: https://github.com/Coder-13-11/bloom-trend-detective

## Project Details

**What it does**
1. **Pick a lake.** Choose one of 121 Florida lakes from a map or a list.
2. **Pick a variable.** Each comes with a one-line definition:
   - *Bloom weeks*: the share of May–October weeks in which the satellite flagged the lake as blooming.
   - *Bloom extent*: the average share of the lake's area above the bloom threshold.
   - *Field chlorophyll*: what boats and volunteers measured in water samples.
   - *Warm-season air temperature* and *rainfall* (NASA MERRA-2).
3. **Get a verdict.** The tool shows the yearly series with its trend line, the rate of change with a 95% range, the p-value, and one of three verdicts: "Significant upward/downward trend", "Possible trend — not significant after accounting for testing many lakes", or "No clear trend yet".
4. **Get a second opinion.** For lakes with both records, the tool says whether satellite and field point the same way over 2020–2025, and how well they agree year to year.

A statewide page lays out the cross-examination as a case: the witnesses, the evidence and the suspects.

**How it works**
- **Satellite bloom labels.** CyAN weekly lake histograms give the lake-median cyanobacteria index. A week is a bloom when the index is ≥ 130 (about 12 µg/L chlorophyll-a), EPA's own threshold. Weeks with less than half the lake visible are "unknown", never "no bloom".
- **Field data.** Chlorophyll-a (corrected for pheophytin) from the Water Quality Portal: Florida LAKEWATCH volunteers, FDEP, counties and water management districts. Stations are assigned to lakes by their position inside the lake outline, with a 150 m tolerance. 2,993 stations fall in 115 of the lakes, giving 26,629 samples.
- **Trend statistics.** Mann-Kendall test (exact for 8 or fewer seasons), Sen's slope with a confidence interval, and Benjamini–Hochberg correction across lakes.
- **Cross-check.** Per-lake slopes for 2020–2025 in both records, with intervals from resampling lakes.
- **Drift test.** For weeks with both a satellite composite and a field sample, we model satellite bloom extent on field chlorophyll, with lake and month fixed effects and a year effect. A year effect above zero means the satellite reads higher for the same field chlorophyll.
- **NASA MERRA-2.** Monthly air temperature and rainfall from NASA POWER, 1981–2025. All 121 lakes show significant warm-season warming, a median +0.28 °C per decade. The lakes share 26 grid cells, so this is regional air, not lake water.
- **Pre-registration.** The rules for every test were written down before its results were computed (protocol Amendments 2–4 in the repo).

**From trend to decision.** EPA publishes a weekly bloom forecast for these lakes. We compared it with "last week's satellite view" twice.
- **Graded against satellite labels** (6,980 lake-weeks): last week's view scored better (Brier score 0.043 vs 0.099).
- **Graded against field samples** (506 lake-weeks in 86 lakes; outcome: field chlorophyll ≥ 12 µg/L): no clear winner. Ranking skill (ROC-AUC) was 0.76 for the forecast and 0.75 for last week's view; the difference was +0.01 (95% CI −0.04 to +0.05).
- **Lesson.** Grading a satellite-based forecast only against satellite labels flatters the rival that uses the same instrument. Independent field data is the fairer judge.

**Benefits.** Students and residents can check a claim like "blooms are getting worse here" against two independent records. Agencies that use satellite indicators get a simple, reproducible check on whether a trend is in the lakes or in the instrument.

**Tools.** Python (pandas, NumPy, SciPy, scikit-learn), Plotly.js, plain HTML/CSS. The site is static, with no server and no login. The statistics have unit tests.

**What we don't claim**
- **Water quality and health.** No toxin, health or water-safety information.
- **Money.** No dollar savings.
- **Causes.** We don't know why the satellite reads higher over time. Instrument drift is one of three suspects, not a finding.
- **Scope.** Florida's satellite-visible lakes only.
- **EPA's model.** No claim that the national forecast is wrong.
- **Known limits.**
  - Field samples measure total chlorophyll at points; the satellite measures a cyanobacteria-related signal over the surface.
  - Lakes share weather, so our intervals are too narrow.
  - 2025–26 field data are still arriving.

**Provenance and timeline.** [TEAM: state honestly what existed before 14 Nov 2026 — e.g. "We researched the topic and wrote a plan before the event; all code, data downloads and analysis in the repository were produced during the hackathon, 14–15 Nov 2026." Adjust to what is true, and ask your Local Lead if unsure.]

## Use of Super Intelligence (SI)
We used an AI assistant (Anthropic's Claude, via Claude Code) to help with the following:
- **Writing code:** data download, statistics, website.
- **Research:** literature and rules checks.
- **Drafting text:** this page and the slides.

How we checked its work:
- Every number shown was produced by the code in the repository from public data.
- One early result was overturned by a later test against field data, and we report both.
- The statistical functions have unit tests, including a brute-force check of the exact Mann-Kendall p-value.
- The trend rules were fixed in writing before any trend was computed.

[TEAM: state honestly where the project idea came from. The 2026 rules say SI should not be used to come up with the idea for solving the challenge.] No images, audio or video in the project are AI-generated. The satellite image is NASA MODIS imagery from Worldview/GIBS.

## NASA Data
- **CyAN Cyanobacteria Index.** CyAN is a joint EPA, NASA, NOAA and USGS project. NASA's Ocean Biology DAAC archives the product, e.g. OLCI Sentinel-3A L3m Inland Waters v5.0, DOI 10.5067/S3A/OLCI/L3M/ILW/5.0 (https://www.earthdata.nasa.gov/data/catalog/ob-cloud-olcis3a-l3m-ilw-5.0). We accessed the weekly lake histograms through the CyAN waterbody service (https://cyan.epa.gov/waterbody/), 121 Florida lakes, 2020–2026.
- **NASA MERRA-2 via NASA POWER** (NASA Langley Research Center), monthly point API, parameters T2M and PRECTOTCORR, 1981–2025 (https://power.larc.nasa.gov/). Used for the warm-season air-temperature and rainfall trends.
- **NASA MODIS Terra corrected-reflectance true colour** via NASA Worldview / GIBS (https://worldview.earthdata.nasa.gov/), Lake Okeechobee, 20 June 2023.

## Space Agency Partner & Other Data
- **ESA / EUMETSAT Sentinel-3 OLCI.** This is the sensor behind the CyAN cyanobacteria index. ESA is a 2026 Space Apps partner agency.
- **U.S. EPA weekly cyanoHAB forecast.** We used the archived 2025–26 table from EPA's public HAB forecast dashboard (https://www.epa.gov/habs/hab-forecasts). We also used the model code from Schaeffer et al. 2024 (DOI 10.23719/1529140) to confirm the bloom threshold.
- **Water Quality Portal (USGS/EPA)** (https://www.waterqualitydata.us/). Florida lake chlorophyll-a corrected for pheophytin, 2000–2026. Data owners include Florida LAKEWATCH, FDEP, counties and water management districts.
- **USGS National Hydrography Dataset** lake outlines and identifiers, via the CyAN waterbody service.
- **Methods references:**
  - Mann (1945), Kendall (1975) and Sen (1968) for the trend test and slope.
  - Gilbert (1987), *Statistical Methods for Environmental Pollution Monitoring*, for the slope confidence interval.
  - Benjamini & Hochberg (1995) for the many-lake correction.
  - Richardson (2000), *Q. J. R. Meteorol. Soc.*, on the economic value of forecasts.
  - Meyers et al. (2025), *Lake and Reservoir Management*, which evaluated the EPA forecast.
  - Stroming et al. (2020), *GeoHealth*, on the value of CyAN information.
  - Coffer et al. (2021), *Water Research*, on how many years of imagery a trend needs.
  - Ho et al. (2019), *Nature*; Wilkinson et al. (2022), *Frontiers in Ecology and the Environment*; Mishra et al. (2023), *Science of the Total Environment*: the published disagreement over bloom trends.
- **Software:** Plotly.js (MIT) for the charts and map outlines.
- **Licence of our code:** Apache-2.0.
