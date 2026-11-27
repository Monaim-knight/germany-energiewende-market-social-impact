# Validation & Data-Quality Evidence

Validation in this project is **risk-driven**: every check corresponds to a concrete schema, ingestion, or interpretation failure mode.

## 1. R Profiling & Grain Validation (`R/01_profile_and_validate_master_panel.R`)

| Check | Result | Decision Informed |
|---|---|---|
| Dimensions & grain | `396` rows × `47` columns; `396` distinct `(geo, year)` keys (`0` duplicates, `0` missing/blank keys) | Confirmed composite primary key `(geo, year)` |
| Panel balance | `36` economies × `11` integer years (`2013–2023`), `0` incomplete economies | Confirmed balanced country-year panel structure |
| Identifier integrity | `36` `geo` ↔ `36` `country_name` 1-to-1 bijection; all `geo` match `^[A-Z]{2}$` | Verified `GE` (Georgia) is never collapsed into `DE` (Germany) |
| Cohort flag stability | `is_eu27` and `is_big6` constant within every economy across all 11 years | Safe to filter static peer cohorts in SQL |
| Whole-number status | `year`, `e_gen_firms_ge5`, `elec_retailers`, `gas_retail_firms_ge5`, `gas_retailers`, `gas_upstream_firms`, `pop` | Assigned `SMALLINT` / `INT` in MySQL DDL |
| Legitimate negatives | `e_cap_net_var_mw`, `elec_price_tax_share_pct`, `gas_price_tax_share_pct`, `utility_arrears_income_gap_pp` | Preserved signed `DECIMAL` types; prevented erroneous `UNSIGNED` or `>= 0` checks |
| Upper-bound check | `ren_elec_pct` reaches `120.01%` (net renewable hydro exporter) | Avoided unsupported `0–100` check constraint on `ren_elec_pct` |

## 2. Observed MySQL Direct-Import Failure & Staging Remediation

An initial direct `LOAD DATA LOCAL INFILE` from `master_panel.csv` into the typed `master_panel` table **failed semantic integrity despite inserting 396 rows**:
- Thousands of warnings were emitted.
- Blank numeric fields (e.g., Austria `e_cap_top`, `e_gen_top`, Bosnia 2013 gas measures) were silently coerced to `0.000`.
- `True`/`False` text strings failed `TINYINT(1)` conversion (Austria `is_eu27` became `0`).
- Decimal-formatted whole-number counts in CSV (e.g., `"4.0"`) failed direct integer casting.

**Remediation:** That direct load was rejected and truncated. An explicit all-`TEXT` staging table (`master_panel_staging`, `sql/02_create_staging_table.sql`) was introduced, followed by a transactional `INSERT ... SELECT` (`sql/04_transform_staging_to_master.sql`) applying `TRIM()`, `NULLIF(..., '')`, explicit `CASE` Boolean mapping, `UPPER(TRIM(geo))`, and two-stage integer casting (`TEXT → DECIMAL(20,6) → UNSIGNED`).

## 3. Final MySQL Reconciliation (`sql/05_reconciliation_checks.sql`)

- **Load summary:** `Records: 396 | Duplicates: 0 | Warnings: 0`.
- **Coverage check:** `total_rows = 396`, `economies = 36`, `first_year = 2013`, `last_year = 2023`, `germany_rows = 11`.
- **Semantic spot-checks (Austria & Germany):**
  - Blank Austria `e_cap_top` and `e_gen_top` remained SQL `NULL` (never `0.000`).
  - Austria flags mapped accurately: `is_eu27 = 1`, `is_big6 = 0`, `in_density_sample = 1`.
  - Decimal precision preserved across `gas_fc_twh` (`DE 2023 = 552.198`) and `retailers_per_twh` (`DE 2023 = 1.762048`).
- **Automated repository tests (`tests/test_pipeline.py`):** Verify 47-column positional alignment between CSV and SQL scripts, zero hardcoded personal paths, Germany 2013/2023 unit checks, exact recalculation of all 5 SQL queries, and SHA-256 manifest hashes.
