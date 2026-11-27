-- ============================================================
-- Germany's Energiewende (2013-2023)
-- MySQL Analytical Layer
-- Step 05: Post-load row and semantic reconciliation checks
-- ============================================================

USE germany_energiewende;

-- 1. Staging vs. final row-count reconciliation (expected: 396 vs 396)
SELECT
    (SELECT COUNT(*) FROM germany_energiewende.master_panel_staging) AS staging_rows,
    (SELECT COUNT(*) FROM germany_energiewende.master_panel) AS final_rows;

-- 2. Panel coverage reconciliation
-- Expected: total_rows=396, economies=36, first_year=2013, last_year=2023, germany_rows=11
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT geo) AS economies,
    MIN(year) AS first_year,
    MAX(year) AS last_year,
    SUM(geo = 'DE') AS germany_rows
FROM germany_energiewende.master_panel;

-- 3. Semantic reconciliation: Austria (AT)
-- Expected: e_cap_top & e_gen_top remain NULL (never coerced to 0),
-- is_eu27 = 1, is_big6 = 0, in_density_sample = 1, decimals preserved.
SELECT
    geo,
    year,
    e_cap_top,
    e_gen_top,
    is_eu27,
    is_big6,
    in_density_sample,
    gas_fc_twh,
    retailers_per_twh
FROM germany_energiewende.master_panel
WHERE geo = 'AT'
ORDER BY year;

-- 4. Semantic reconciliation: Germany (DE)
-- Expected: 11 rows (2013-2023), is_eu27 = 1, is_big6 = 1, in_density_sample = 1,
-- 2013 e_cap_top = 29.000, e_gen_top = 32.000, 2023 gas_fc_twh = 552.198.
SELECT
    geo,
    year,
    e_cap_top,
    e_gen_top,
    is_eu27,
    is_big6,
    in_density_sample,
    gas_fc_twh,
    retailers_per_twh
FROM germany_energiewende.master_panel
WHERE geo = 'DE'
ORDER BY year;
