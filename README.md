# BloomEconomics / Bloom Trend Detective

NASA Space Apps 2026 entry for **Be An Earth System Trend Detective!** Satellites say Florida's lakes are getting greener. This project tests whether that trend can be trusted, by cross-examining the satellite cyanobacteria index (CyAN) against independent field chlorophyll samples, lake by lake. It also provides NASA MERRA-2 temperature and rainfall trends, and asks whether the weekly bloom forecast is worth acting on.

- Live site: `site/` (static; serve with `python3 -m http.server --directory site`)
- Slides: `submission/BloomTrendDetective_slides.pdf`
- Project-page text: `submission/project_page.md`
- Results: `research/results_crosscheck_v1.md`, `research/results_trends_v1.md`, `research/results_v1.md`
- Review that led to the pivot: `reports/Critical review and pivot plan.md`

**Use of AI.** The code, analysis and text were written with an AI assistant (Anthropic's Claude, via Claude Code). Every number comes from the code here, run on public data; the statistics have unit tests. No images are AI-generated. All source files in `src/`, `scripts/`, `tests/` and `site/` were AI-assisted.

**Licence.** Code: Apache-2.0 (see `LICENSE`). Third-party: Plotly.js 2.35.2 (MIT) and its US map outlines are bundled in `site/vendor/`. Satellite image: NASA Worldview/GIBS. Data belong to their providers (EPA/NASA/NOAA/USGS CyAN, NASA POWER, Water Quality Portal contributors); see `docs/source_manifest.csv`. Raw downloads are not in the repository; the manifest lists every URL and checksum.

---

## Research prototype (Arm A)

**Status (2026-11-15):** Space Apps submission rebuilt around a field cross-check of the satellite trend (protocol Amendments 2–4). Research gates: G0, G1 passed; G3 failed for dollar savings; G2 done for Florida 2025–26, and re-scored against field data.
All data are real public data unless an output is labelled `SCENARIO`. No result here is an observed saving.

## Question
When is earlier satellite-informed cyanobacterial-bloom information worth acting on? Re-scoped after
Phase 0 to a measurable question (see `research/protocol.md`): across cost/loss ratios, does acting on the
operational EPA weekly cyanoHAB forecast beat acting on last week's satellite observation (persistence) for
Florida lakes in 2025–26, and is the advantage concentrated on bloom onsets?

## Phase 0 findings (verified against sources)
| Finding | Evidence |
|---|---|
| EPA's INLA data DOI contains code only — no predictions | `data/raw/D02_inla/` (D-002) |
| An archive of the operational forecasts exists inside the EPA dashboard (Qlik); exported 148,988 lake-weeks, 2025–2026 only, no issue timestamps | `scripts/qlik_export.py`, D-003/D-004 |
| INLA model uses temperature, precipitation, morphology, seasonal AR1 and space; **no lagged bloom state** | `conus_inla.R` L199 |
| Bloom label = lake median CyAN DN ≥ 130 (≈12 µg/L) | `cyan_processing_conus.R` L170 |
| Lake Okeechobee: 15 lake-median bloom weeks in 2020–26, though up to 94 % of pixels exceeded the threshold in some weeks | `outputs/report/okeechobee_by_year.csv` |
| The only costed Okeechobee intervention (USGS HABITATS, 2018 scenario) needs p ≥ 0.91 to break even even with byproduct sales (> 1 without); Okeechobee's max EPA weekly p in 2025–26 was 0.23 | `outputs/report/habitats_break_even.csv`, D-011 |
| Operational verification (Meyers et al. 2025) and VOI of satellite HAB info (Stroming 2020, Pindilli 2022, Tzimas 2024, Newbold 2022) are established | `research/prior_art.md` |

## Reproduce
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python -m bloom.ingest --config config/sources.yaml   # hours: CyAN API is slow
PYTHONPATH=src .venv/bin/python -m bloom.report                                # inventory, Okeechobee, scenario
PYTHONPATH=src .venv/bin/python -m bloom.backtest --config config/experiment.yaml
PYTHONPATH=src .venv/bin/python -m bloom.trends --config config/trends.yaml     # CyAN trends (Amendment 2)
PYTHONPATH=src .venv/bin/python -m bloom.power --config config/trends.yaml      # NASA POWER / MERRA-2 trends
PYTHONPATH=src .venv/bin/python -m bloom.insitu                                # field cross-check (Amendment 3); needs data/raw/D10_wqp, D11_lake_geom
PYTHONPATH=src .venv/bin/python -m bloom.fieldtruth                            # drift + field-truth forecast tests (Amendment 4), ~12 min
PYTHONPATH=src .venv/bin/python -m bloom.site_data                             # site/data/site.json
.venv/bin/pytest
```
The forecast archive is re-exported with
`python scripts/qlik_export.py 9727f5d1-11d5-4522-9a59-1835a1885159 AllWeeks_CyanForecasts <out.csv>`;
the dashboard is live, so a new export will contain more weeks than the one archived here (SHA-256 in
`docs/source_manifest.csv` / `.meta.json`).

## Layout
`research/` protocol, prior art, decision log, limitations · `config/` sources, experiment, scenarios ·
`docs/` source manifest, cost ledger · `src/bloom/` ingest, normalize, labels, lakemap, economics,
backtest, scenario, report · `tests/` · `outputs/`.

## Claim limits
No toxin/health validity; no avoided-damage or taxpayer-savings estimate; satellite labels only;
forecast issue times unknown; Florida resolvable lakes only. See `research/limitations.md`.
