# Decision log

Format: ID · date · decision · evidence · assumptions / consequences.

**D-001 · 2026-11-14 · New scratch project, not prior CyFi/BloomScout work.** Related folders exist on this machine (`FTIR Identification Improved ISEF 2027/…/bloomscout`, `~/Downloads/BloomScout_Research_Plan.pdf`). Per master plan §0/§10, they were **not read or used**; all work here is event-period work. Provenance review of those files remains optional.

**D-002 · D02 is code only.** `INLA_CONUS_forecast.zip` (33,677 bytes, SHA-256 126f7f3f…) contains 11 R scripts + README, no inputs, outputs or predictions. Consequence: D02 cannot supply archived forecasts; it does supply the exact label rule and model formula.

**D-003 · Forecast archive obtained from the EPA dashboard back-end.** The EPA forecast page embeds three Qlik Sense apps. The public Engine API (anonymous, read-only) exposes table `AllWeeks_CyanForecasts`; exported all 148,988 raw rows with `GetTableData` (no aggregation). Coverage: 2025 (35 weeks) and 2026 (33 weeks), 2,191 lakes. Earlier operational years (2021–2024) are **not** in this archive.

**D-004 · Issue time unknown → `retrospective_flag = unknown_issue_time`.** The table has valid week only. App reload 2026-11-10T01:00Z already contained the week 2026-11-08…14, suggesting forecasts for week W appear early in week W. We cannot verify whether past rows were overwritten by re-runs. Consequence: results describe *the archived forecast*, not proven issued-as-of skill.

**D-005 · Outcome source = CyAN waterbody API weekly composites.** `cyan.epa.gov/waterbody/data/?OBJECTID=…&daily=False` returns per-week 256-bin DN histograms keyed by Sunday start. Multi-year requests time out (504) → one request per year. 2016–2019 returned 0 records for Okeechobee; record starts 2020.

**D-006 · Label reproduction.** EPA rule: `bloom = median >= 130` over pixels with `coverage_fraction == 1` within resolvable lake polygons (cyan_processing_conus.R L105–170). We compute the median over DN 0–253 from the API histogram. Pixel sets may differ (API polygon handling unknown). Not validated against EPA's own labels (none published in the dashboard apps).

**D-007 · DN conventions.** 0 = below detection, 1–253 valid, 254 land, 255 no data; chl-a ≈ 6620·10^(3/250·DN − 4.2) − 3.1 gives DN 130 ≈ 12.07 µg/L, matching EPA's "130 for 12 ug/L" comment. To re-verify against the CyAN product guide.

**D-008 · Lake ID crosswalk.** Forecast `COMID` ≠ CyAN `OBJECTID` (Okeechobee 166757656 vs 6624886). Matched by name search + nearest centroid within max(3 km, 0.6·√area). 121/132 FL lakes matched, 9 no candidate, 2 beyond tolerance (Lake Ocklawaha 3.3 km vs 3.0 km — likely correct but excluded per the rule fixed in advance). No duplicate OBJECTIDs.

**D-009 · Lake-wide label is a poor proxy for Okeechobee hazard.** 2020–2026: only 15 bloom-labelled weeks; yet weeks with 20–94% of valid pixels above DN 130 are common. For a 1,296 km² lake with patchy/shoreline blooms the lake median is conservative. Consequence: the EPA endpoint is not the downstream-discharge hazard that drives the USGS damages.

**D-010 · USGS HABITATS treated as a transfer boundary case only.** Table 13 capex ($674k) is described as amortized over 20 years at 5%; whether Table 15 adds an annualised share or full capex is ambiguous in the text. Used Table 15/16 totals as reported. eL taken directly from Table 16 "Deployment benefits". Ancillary products treated as event-conditional revenue (no biomass, no product) and their market is undemonstrated (report p.19–20), so p* is reported with and without them.

**D-011 · G3 outcome.** p* ≥ 0.91 for all four scenarios with ancillary revenue; > 1 for all without. Max EPA weekly p for Okeechobee 2025–26 = 0.234. Forecast-guided HABITATS deployment never triggers; the oracle upper bound on value is ≤ $0.83M per 2018-like event and only with saleable byproducts. Also: forecast is lake-scale, damages are downstream-site-scale (master plan §3) — the equation is not formally valid without a linkage model, which does not exist here.

**D-012 · Tie convention.** Act iff p > p* (strict). At equality the expected costs are identical; deferring is chosen. Tested.

**D-013 · Research question re-scoped** to cost-loss verification vs persistence (see protocol.md). Reason: savings estimation fails G3; REV curves state value conditional on α without assuming efficacy.

**D-014 · Validity threshold for outcomes.** Week label `unknown` if < 50% of water pixels (valid + no-data) are valid. Prespecified; not tuned.

**D-015 · Download concurrency** limited to 6 threads; atomic writes (`.part` → rename) after an interrupted sequential run. All saved JSON re-parsed successfully before resuming.

**D-016 · Primary run on 2025–26 with secondary baselines deferred** (Amendment 1). `config/experiment_primary.yaml`, output `outputs/fl_v1_primary/`.

**D-017 · Exploratory analyses E1 (new-episode onsets, 4 prior known non-bloom weeks) and E2 (hybrid persistence-or-forecast rule)** were defined *after* seeing primary results. Labelled EXPLORATORY in every output; not used for confirmatory claims.

**D-018 · Full run with secondary baselines** after the 2020–2024 download completed (no failed lake-years). Training 2020–2023 exactly as originally prespecified; output `outputs/fl_v1/`. Logistic coefficients in `run_manifest.json`.

**D-019 · Exploratory latency check:** logistic refit on W−2 features only, to address whether the logistic's advantage depends on last week's composite being available. Defined after seeing results; labelled EXPLORATORY.

**D-020 · Data request to EPA drafted, not sent** (2026-11-14). `docs/epa_data_request_draft.md`. It asks for:
- EPA's weekly lake labels;
- pixel rules and product version;
- 2025–26 issue dates;
- 2021–24 forecasts;
- composite latency.

The recipient is the contact point listed in the data.gov record for DOI 10.23719/1529140, not a guessed address. Sending is the user's decision and is done from their own account. The draft gives no numbers and frames the result as possibly a label artefact. If labels arrive, the re-analysis will be pre-registered before it is run.

**D-021 · Re-scoped for the Space Apps challenge "Be An Earth System Trend Detective!"** (2026-11-15). The challenge scores trend detection and significance testing on a NASA variable for a region. The decision-economics result is kept as the "so what" section. Dropped from the submission:
- dollar and HABITATS figures;
- the logistic-beats-EPA headline;
- E1, E2 and the lag-2 logistic check.

Rationale and sources: `reports/NASA Space Apps submission strategy.md`.

**D-022 · Trend protocol (Amendment 2)** was written before any trend was computed. It covers season May–October, annual aggregation, Mann-Kendall (exact for n ≤ 8), Sen's slope with a Gilbert CI, and BH correction across lakes for the CyAN variables. MERRA-2 is not BH-corrected because lakes share grid cells.

**D-023 · NASA MERRA-2 via the NASA POWER monthly API** (no login), added as the clearly-NASA variable. 121 files, manifest rows D09-power-*.

**D-024 · Statewide yearly view added post hoc** after seeing the lake results. It is labelled EXPLORATORY and presented as an open "real or instrument?" question.

**D-025 · Static site** (`site/`) with Plotly 2.35.2 and the US topojson vendored locally. The cdnjs path returned 404, and a local copy means judges don't depend on a CDN. The 7-slide PDF is exported with headless Chrome from `site/slides.html`.

**D-026 · Critical review (2026-11-15).** The 7-season trend picker is underpowered and overlaps published work (Coffer 2021; Schaeffer 2022; Mishra 2023). The savings premise remains unsupported. Chosen direction to propose: cross-examine the satellite trend against independent field data. See `reports/Critical review and pivot plan.md`.

**D-027 · Field cross-check (Amendment 3)** was pre-registered before any field value was analysed.
- Data: Water Quality Portal Florida lake chlorophyll-a (corrected), 2000–2026, 146,396 rows, manifest rows D10-wqp-*.
- Lake polygons: CyAN geometry service, manifest rows D11-geom-*.
- Matching: point-in-polygon with 150 m tolerance. 2,993 stations in 115 lakes.

**D-028 · Result of Amendment 3.**
- Primary verdict: "Corroborated". Field median +7.5% per year [2.6, 13.2], 45 lakes, 2020–2025. Within-lake ρ 0.30.
- Not shown: lake-level slope agreement (ρ 0.12, CI includes 0).
- Exploratory: field chlorophyll eased after 2023 while the satellite kept rising.
- Long record: 13 lakes with ≥ 15 seasons, none significant.
- Outputs: `outputs/insitu_v1/`.

The time-to-detect estimate (Weatherhead) is computed but not used in claims. It reuses the slope estimated from the same short series, so it is optimistic.

**D-029 · Pivot approved by the user** (2026-11-15): cross-examine the satellite trend with field data. Amendment 4 was pre-registered before E2 and E3 ran.

**D-030 · Results of Amendment 4.**
- E2: year slope +2.46 points per year [1.40, 3.62]. The satellite reads higher for the same field chlorophyll in later years.
- E3: AUC difference EPA − last week's extent +0.007 [−0.039, 0.050]. No difference shown.

The earlier satellite-graded result (results_v1) is kept and relabelled; it is not deleted. See `research/results_crosscheck_v1.md`.

**D-031 · Sample-count correction.** The public claim uses 26,629 records, the number in the matched lakes. The statewide download total is 141,907 and is not used as a claim.

**D-032 · Per-lake field trend for the tool.** It uses all well-sampled seasons 2000–2025 (≥ 6 seasons), BH-corrected across 65 lakes. Amendment 3's long-record secondary specified ≥ 15 seasons; both are reported. The lake-level "second opinion" text reports slope directions only, because P2 showed no lake-level slope agreement.

**D-033 · Site and slides rebuilt** around three findings (satellite rising; field agrees on direction; satellite reads higher at fixed field chlorophyll) and a two-grader decision section. "No clear winner" replaces "tie" as the wording for E3.
