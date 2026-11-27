# Data Directory

All project data derives from **eight official Eurostat datasets** covering 36 European economies over 2013–2023. No personal, confidential, or microdata records are stored in this repository.

## Folder Structure

- `data/raw/estat_nrg_ind_market.tsv` — Original Eurostat energy market indicators extract (`nrg_ind_market`).
- `data/external/` — Cached Eurostat Dissemination API v1.0 CSV extracts for final gas consumption (`nrg_bal_s`), population (`demo_pjan`), renewable energy shares (`nrg_ind_ren`), household electricity prices (`nrg_pc_204`), household gas prices (`nrg_pc_202`), thermal hardship (`ilc_mdes01`), and utility arrears (`ilc_mdes07`).
- `data/processed/master_panel.csv` — Validated balanced country-year panel (`396` rows × `47` columns; composite primary key `(geo, year)`), built by `src/energiewende/ingestion.py`, profiled by `R/01_profile_and_validate_master_panel.R`, and loaded into MySQL (`germany_energiewende.master_panel`) via `sql/02`–`sql/04`.
- `data/manifest.json` — Machine-generated provenance log containing exact Eurostat API query URLs, retrieval UTC timestamps, row counts, and SHA-256 checksums for every input file and the processed panel.

## Attribution & Reuse

Source data is published by **Eurostat** under the European Commission open-data reuse notice (attribution required; modifications documented in `docs/data_provenance.md` and `docs/data_dictionary.md`).
