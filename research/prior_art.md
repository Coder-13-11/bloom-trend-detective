# Prior art and originality assessment (2026-11-14)

## Search log
| # | Date | Database / route | Query | Results kept |
|---|---|---|---|---|
| S1 | 2026-11-14 | Consensus (Semantic Scholar/OpenAlex/PubMed), 25 results | "value of information cyanobacterial harmful algal bloom forecast decision cost-loss" | raw: `research/lit/consensus_q1_voi.json` |
| S2 | 2026-11-14 | Consensus, 5 results | "Meyers National forecasting of cyanobacterial harmful algal bloom events 3-year model evaluation" | Meyers 2025 |
| S3 | 2026-11-14 | Consensus, 15 results | "relative economic value cost-loss ratio verification harmful algal bloom forecast persistence baseline" | none directly on cyanoHAB REV |
| S4 | 2026-11-14 | Crossref API | DOIs of plan-cited papers 1–4 | metadata verified |
| S5 | 2026-11-14 | EPA code archive (DOI 10.23719/1529140) | read `conus_inla.R`, `cyan_processing_conus.R` | model formula, label rule |

**Not done yet:** forward/backward citation chasing; Web of Science/Scopus; grey literature
(FDEP, SFWMD, USACE reports); full-text reading of most papers below (abstract-level only
unless stated). A search failure is not proof of novelty.

## Closest work — what each establishes
| Paper | Read level | Method | Data / outcome | Overlap with this project |
|---|---|---|---|---|
| Schaeffer et al. 2024, J Env Mgmt 349:119518 (DOI verified) | abstract + **code** | INLA Bayesian spatiotemporal; predictors: water temp, precip, area, depth, AR1(week-of-year), SPDE space. **No lagged bloom state** (conus_inla.R L199) | CyAN label median DN ≥130; train 2017–20, test 2021: acc 90%, sens 88%, spec 91%, precision 49% | Source of the forecast evaluated here |
| Meyers et al. 2025, Lake Reserv Mgmt | abstract | Operational evaluation of 2021–23 predictions, FN/FP characterisation | 331,049 lake-weeks; FN 1.34%, FP 8.06%; FPs cluster before/after/between real blooms | **Operational verification is established.** Our 2025–26 verification is an out-of-period extension, not new. Their FP pattern suggests persistence comparison is informative |
| Stroming et al. 2020, GeoHealth (DOI verified) | abstract | Impact assessment, Utah Lake 2017, satellite-informed advisories | ~$370k health benefits (plan figure, not re-verified in full text) | VOI of satellite detection for advisories established |
| Pindilli et al. 2022, Front Env Sci | abstract | Bayesian decision tree VOI, 2-day earlier toxicity warning, Kansas | recreation + health | VOI of cyanoHAB early warning established |
| Tzimas et al. 2024, IGARSS | abstract | Decision-theoretic VoI: EO forecasting/monitoring vs regular monitoring, accuracy vs in-situ 2015–19 | Lake Harsha (OH) | **Very close:** VOI of EO forecasts vs existing monitoring. Single lake, in-situ labels |
| Luhede et al. 2024, J Env Mgmt | abstract | VoI theory for HAB prediction (act now vs collect data) | — | VOI framing for HAB prediction established |
| Newbold et al. 2022 (RePEc WP) | abstract | Information valuation framework, recreation site choice, 100 CA lakes, SFEI satellite data | California 2019 | Multi-lake economic value of satellite HAB info established |
| Jacobs, van Voorn, van Heijster, Hengeveld 2024, Ecol Model (DOI verified) | **title/metadata only** (no abstract via Crossref) | per master plan: prevention vs reactive vs delayed resetting vs nothing under alternative stable states | dynamical models | Cost-aware timing of control is not new (per plan; to be read in full) |
| Boubacar et al. 2024, USGS SIR 2024-5091 | **full text, Tables 1,5,8–16 extracted** | Scenario CBA of HABITATS, 2018 Okeechobee event | $7.8M damages (lower bound); net −$2.11M…+$0.83M | Sole costed Okeechobee intervention; used here as transfer scenario |
| Stumpf et al. 2008, J Mar Sys | abstract | Skill of operational Karenia brevis forecast; resolution-matched validation | SW Florida | Precedent for matching forecast and validation scale |
| Jin et al. 2008 (Harmful Algae); Jin et al. 2024 (ICES JMS) | abstract | VOI of HAB forecasts for fisheries | Gulf of Maine; PNW | Marine VOI precedent |
| Richardson 2000, QJRMS 126:649 | known method (not re-read) | Relative economic value / cost-loss | weather forecasts | Method used here; not new |

## Distinction table — candidate contribution vs closest work
| Element | Schaeffer 24 | Meyers 25 | Tzimas 24 | Newbold 22 | **This project** |
|---|---|---|---|---|---|
| Forecast evaluated | own INLA, 2021 | operational INLA, 2021–23 | PrimeWater services | satellite detection (not forecast) | operational INLA as archived, **2025–26** |
| Compared against persistence of last satellite observation | not reported in abstract | not reported in abstract | vs regular monitoring | n/a | **yes, plus lag-2 sensitivity** |
| Onset-specific evaluation | no (abstract) | FN timing discussed | ? | n/a | **yes** |
| Economic metric | none | none | VoI (single lake) | WTP / site choice | **REV over cost/loss ratio**, multi-lake, clustered CI |
| Intervention costs | none | none | monitoring/health/recreation | recreation | USGS HABITATS as boundary case only |

**Defensible originality statement (provisional):** We did not find (in searches S1–S3) a
published cost-loss / relative-economic-value comparison of the operational EPA cyanoHAB
forecast against a persistence-of-observation baseline, nor an onset-specific evaluation of
it. This is an *incremental, verification-focused* contribution using established methods.
It is not a new forecasting method and not the first VOI analysis of satellite HAB information.
