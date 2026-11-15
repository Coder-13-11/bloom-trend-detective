# Limitations and unresolved questions

## Data and labels
1. **Satellite labels, not toxins.** Outcome = CyAN lake-median DN ≥ 130 (~12 µg/L chl-a). Says nothing about microcystin or health risk. Forecast and label share the same satellite product family, so evaluation is not independent of the sensor.
2. **Label reproduction is approximate.** API histogram pixel set ≠ EPA's `coverage_fraction == 1` resolvable mask; CyAN product version not reported by the API; possible reprocessing since forecasts were made.
3. **Issue time unknown.** The archive has valid weeks but no issue/availability timestamps, and we cannot rule out retrospective re-runs overwriting rows. Persistence timing (W−1 composite available when the W forecast is used) is assumed comparable; the lag-2 sensitivity is the conservative check.
4. **Short archive.** Forecasts only for 2025–2026 (~68 weeks). Operational 2021–2024 forecasts were evaluated by Meyers et al. 2025 but are not in this archive.
5. **Lake-scale endpoint.** For large lakes (Okeechobee 1,296 km²) the lake median misses patchy, shoreline and embayment blooms (EPA's own caveat). Lakes too small/narrow for OLCI are absent.
6. **Crosswalk errors.** Name + centroid matching may mis-assign same-named lakes; 11/132 FL lakes excluded.
7. **Missing weeks** (clouds, sensor gaps) are `unknown`; if missingness correlates with blooms (e.g. summer convection), results are biased in an unknown direction.

## Economics
8. **No observed intervention efficacy or agency expenditure** was obtained (D09 not acquired). All costs are modeled (USGS 2018, 2018 USD) or planning estimates (BMAP). Nothing here is a taxpayer saving.
9. **HABITATS transfer** combines a 2018 event's damages/costs with 2025–26 forecasts; downstream-site damages vs lake-scale probability; possible recreation/property double counting inherited from the source; ancillary-product markets undemonstrated.
10. **REV assumes** a static binary protect/don't decision per lake-week, a constant α, fully avoidable eL at fixed cost, independence across weeks, and no capacity constraint. Real actions (sampling campaigns, advisories) have latency, episode-level commitment and fixed mobilisation costs.
11. **Cost-loss α for real Florida actions is unknown.** The REV curve shows where value would exist; placing an agency action on it needs documented C, e and L.

## Unresolved research questions
- Q1 What is the documented cost, latency and decision rule for FDEP/SFWMD confirmatory sampling triggered by satellite signals? (Would place A1 on the REV curve.)
- Q2 Does an extent-based endpoint (fraction of pixels ≥ DN130) better track FDEP field microcystin detections at Okeechobee than the lake median? (Needs D04 FDEP sampling data — not yet downloaded.)
- Q3 Can EPA provide issue-time-stamped forecast archives, including 2021–2024? Request drafted, not sent (`docs/epa_data_request_draft.md`, D-020).
- Q4 Is there any lake-to-structure linkage (S-77, S-308 discharge sampling) that converts lake-scale p into site risk?
- Q5 (Arm B) Whether any long-term intervention record supports a causal restoration-cost analysis — not started; the plan's conditions are not met.

## Added after v1 results
12. **Shared-sensor autocorrelation favours persistence.** Persistence and the outcome come from the same CyAN product, so sensor/processing artifacts that persist week to week help persistence. Field-validated outcomes might narrow its advantage.
13. **Onset flicker.** Lake medians near DN 130 cross the threshold repeatedly; many primary-analysis "onsets" are re-crossings (see E1).
14. **Decision rule assumes calibration** (act iff p > α). EPA probabilities are miscalibrated in the tails; a recalibrated forecast could do better. Recalibration must be fitted on a season other than the test season.
15. **The lag-2 logistic latency check (D-019) has no generating script in `src/` or `scripts/`.** It is not reproducible as it stands, so it was cut from the submission until it is scripted.
16. **Trends rest on 7 seasons.** Power is low, so "no clear trend" means not shown, not shown to be flat.
17. **Possible CyAN product drift.** The coherent statewide rise in 2020–2026 (results_trends_v1.md) cannot be separated from sensor or processing changes without independent field data.
18. **MERRA-2 is a coarse reanalysis.** The grid is about 50 km, and 121 lakes fall in 26 cells. It is not lake-water temperature.
19. **Field and satellite measure different things.** The field data are total chlorophyll at sampling points; the satellite measures a cyanobacteria-related signal over the lake surface. Agreement in direction is informative; agreement in size is not expected.
20. **Field reporting lag.** 2026 field data are about 30% complete, and 2025 may be incomplete (fewer sampling dates per lake). The primary window is 2020–2025; the 2020–2026 sensitivity is not reliable.
21. **Station matching** uses NHD outlines with a 150 m tolerance. Stations in canals or marinas next to a lake may be included.
22. **Limitation 12 confirmed in practice.** Against field data (E3) the satellite-graded advantage of persistence over the EPA forecast disappears.
23. **Field data downloads are not scripted in `ingest.py`.** The Water Quality Portal and lake-outline downloads were run as one-off commands. URLs and checksums are in the manifest (D10-wqp-*, D11-geom-*), but a clean re-download needs those commands moved into a script.
24. **The drift-test year effect leans high.** Measurement noise in field chlorophyll attenuates its coefficient, which can inflate the year effect.
