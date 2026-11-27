# Data Provenance & Lineage

All statistical series in this project originate from **Eurostat** (European Commission) and follow official indicator codes from the **European Environment Agency (EEA)** Eurostat vocabulary (`indic_nrgm`). Full API query URLs, retrieval UTC timestamps, row counts, and SHA-256 checksums are logged in [`data/manifest.json`](../data/manifest.json).

## Verified Input Sources (8 Datasets)

| Local File | Provider & Dataset Code | Extraction / Dataset Update Metadata | Coverage |
|---|---|---|---|
| `data/raw/estat_nrg_ind_market.tsv` | **Eurostat** `nrg_ind_market` (Energy market indicators) | Local TSV extract; SHA-256 recorded in `data/manifest.json` | 36 economies, 2013–2023 (2024 dropped as sparse) |
| `data/external/gas_final_consumption.csv` | **Eurostat** `nrg_bal_s` (`FC_E + FC_NE`, `G3000`, `GWH`) | Cached Eurostat API extract; verified in `data/manifest.json` | Annual, 2013–2023 |
| `data/external/population_1january.csv` | **Eurostat** `demo_pjan` (`TOTAL`, sex `T`, `NR`) | Cached Eurostat API extract; verified in `data/manifest.json` | Annual, 2013–2023 |
| `data/external/renewables_share.csv` | **Eurostat** `nrg_ind_ren` (`REN`, `REN_ELC`, `PC`) | Eurostat updated `2026-09-15`; fetched `2026-11-23 UTC` (`409` rows) | Annual, 2013–2023 |
| `data/external/household_elec_prices.csv` | **Eurostat** `nrg_pc_204` (`E7000`, `KWH2500-4999`, `I_TAX` & `X_TAX`, `EUR` & `PPS`) | Eurostat updated `2026-10-19`; fetched `2026-11-23 UTC` (`457` rows) | Bi-annual (`S1`/`S2`) averaged to annual means, 2013–2023 |
| `data/external/household_gas_prices.csv` | **Eurostat** `nrg_pc_202` (`G3000`, `GJ20-199`, `I_TAX` & `X_TAX`, `EUR` & `PPS`) | Eurostat updated `2026-10-19`; fetched `2026-11-23 UTC` (`367` rows) | Bi-annual (`S1`/`S2`) averaged to annual means, 2013–2023 |
| `data/external/energy_poverty_warmth.csv` | **Eurostat** EU-SILC `ilc_mdes01` (`hhcomp=TOTAL`, `rskpovth=TOTAL/B_60/A_60`, `PC`) | Eurostat updated `2026-10-20`; fetched `2026-11-23 UTC` (`453` rows) | Annual, 2013–2023 |
| `data/external/utility_arrears.csv` | **Eurostat** EU-SILC `ilc_mdes07` (`hhcomp=TOTAL`, `rskpovth=TOTAL/B_60/A_60`, `PC`) | Eurostat updated `2026-10-20`; fetched `2026-11-23 UTC` (`453` rows) | Annual, 2013–2023 |

## End-to-End Transformation Chain

1. **Upstream Assembly (`src/energiewende/eurostat.py`, `src/energiewende/ingestion.py`):** Parses `estat_nrg_ind_market.tsv` (mapping `:` to `NULL`, stripping Eurostat status flags), averages bi-annual S1/S2 household prices to annual means, left-joins all 7 external CSVs onto `(geo, year)` over 2013–2023, derives 8 analytical fields, enforces Germany-2013 unit checks, and writes `data/processed/master_panel.csv` (`396 × 47`) plus `data/manifest.json`.
2. **Independent Grain & Datatype Profiling (`R/01_profile_and_validate_master_panel.R`):** Validates panel dimensions, key uniqueness, 11-year balance, bidirectional `geo ↔ country_name` mapping, cohort flag stability, 47-column role classification, and schema-relevant datatype bounds before database design.
3. **Typed Analytical Storage (`sql/00`–`sql/05`):** Loads raw CSV text into `master_panel_staging` (`TEXT`), executes explicit type/NULL/Boolean/two-stage-integer conversions into `germany_energiewende.master_panel`, and reconciles row counts and semantic values.
4. **Analytical Queries & Presentation Views (`sql/06`–`sql/07` → Tableau):** Computes all five headline questions and exposes five presentation-ready views (`vw_tableau_*`) consumed directly by the Tableau executive dashboard.

## Redistribution & Source Limitations

- **Redistribution:** Eurostat open data may be reused with source attribution under the European Commission reuse policy. No personal or confidential microdata is stored in this repository.
- **Known source caveats:** Eurostat `nrg_ind_market` reporting is voluntary and uses `:` identically for unavailable and confidential cells; EU-SILC `ilc_mdes01` had a documented sampling/methodology break for Germany in 2020; Eurostat `nrg_ind_ren` electricity shares (`REN_ELC`) can exceed 100% in net hydro exporters (e.g., Norway).
