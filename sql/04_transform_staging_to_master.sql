-- ============================================================
-- Germany's Energiewende (2013-2023)
-- MySQL Analytical Layer
-- Step 04: Controlled transformation from staging to master_panel
--
-- Explicit rules enforced:
-- - TRIM() removes incidental whitespace
-- - NULLIF(..., '') converts blank CSV cells to SQL NULL (never 0)
-- - CASE maps 'true'/'false' text explicitly to 1/0
-- - Two-stage cast (TEXT -> DECIMAL(20,6) -> UNSIGNED) safely parses
--   decimal-formatted whole-number counts such as "4.0" -> 4
-- - UPPER(TRIM(geo)) normalizes two-letter country codes
-- - Executed inside a transaction; expected: 396 rows, 0 warnings
-- ============================================================

USE germany_energiewende;

-- Optional safeguard for full reload (uncomment intentionally):
-- TRUNCATE TABLE germany_energiewende.master_panel;

START TRANSACTION;

INSERT INTO germany_energiewende.master_panel (
    geo,
    year,
    e_cap_connected_mw,
    e_cap_decomm_mw,
    e_cap_net_var_mw,
    e_cap_share,
    e_cap_top,
    e_gen_firms_ge5,
    e_gen_share,
    e_gen_top,
    elec_retailers,
    gas_retail_firms_ge5,
    gas_retail_share_ge5,
    gas_retailers,
    gas_upstream_firms,
    fc_e_gwh,
    fc_ne_gwh,
    gas_fc_gwh,
    pop,
    ren_total_pct,
    ren_elec_pct,
    elec_price_eur_kwh,
    elec_price_extax_eur_kwh,
    elec_price_pps_kwh,
    elec_price_tax_share_pct,
    gas_price_eur_kwh,
    gas_price_extax_eur_kwh,
    gas_price_pps_kwh,
    gas_price_tax_share_pct,
    unable_warm_above60_pct,
    unable_warm_lowinc_pct,
    unable_warm_total_pct,
    unable_warm_income_gap_pp,
    utility_arrears_above60_pct,
    utility_arrears_lowinc_pct,
    utility_arrears_total_pct,
    utility_arrears_income_gap_pp,
    country_name,
    is_eu27,
    is_big6,
    gas_fc_twh,
    retailers_per_twh,
    in_density_sample,
    retailers_per_million,
    e_cap_other_major_share,
    e_gen_other_major_share,
    e_cap_gross_churn_mw
)
SELECT
    UPPER(TRIM(geo)),
    CAST(CAST(NULLIF(TRIM(year), '') AS DECIMAL(20,6)) AS UNSIGNED),

    CAST(NULLIF(TRIM(e_cap_connected_mw), '') AS DECIMAL(12,3)),
    CAST(NULLIF(TRIM(e_cap_decomm_mw), '') AS DECIMAL(12,3)),
    CAST(NULLIF(TRIM(e_cap_net_var_mw), '') AS DECIMAL(12,3)),
    CAST(NULLIF(TRIM(e_cap_share), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(e_cap_top), '') AS DECIMAL(8,3)),

    CAST(CAST(NULLIF(TRIM(e_gen_firms_ge5), '') AS DECIMAL(20,6)) AS UNSIGNED),
    CAST(NULLIF(TRIM(e_gen_share), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(e_gen_top), '') AS DECIMAL(8,3)),
    CAST(CAST(NULLIF(TRIM(elec_retailers), '') AS DECIMAL(20,6)) AS UNSIGNED),

    CAST(CAST(NULLIF(TRIM(gas_retail_firms_ge5), '') AS DECIMAL(20,6)) AS UNSIGNED),
    CAST(NULLIF(TRIM(gas_retail_share_ge5), '') AS DECIMAL(8,3)),
    CAST(CAST(NULLIF(TRIM(gas_retailers), '') AS DECIMAL(20,6)) AS UNSIGNED),
    CAST(CAST(NULLIF(TRIM(gas_upstream_firms), '') AS DECIMAL(20,6)) AS UNSIGNED),

    CAST(NULLIF(TRIM(fc_e_gwh), '') AS DECIMAL(12,3)),
    CAST(NULLIF(TRIM(fc_ne_gwh), '') AS DECIMAL(12,3)),
    CAST(NULLIF(TRIM(gas_fc_gwh), '') AS DECIMAL(12,3)),
    CAST(CAST(NULLIF(TRIM(pop), '') AS DECIMAL(20,6)) AS UNSIGNED),

    CAST(NULLIF(TRIM(ren_total_pct), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(ren_elec_pct), '') AS DECIMAL(8,3)),

    CAST(NULLIF(TRIM(elec_price_eur_kwh), '') AS DECIMAL(10,6)),
    CAST(NULLIF(TRIM(elec_price_extax_eur_kwh), '') AS DECIMAL(10,6)),
    CAST(NULLIF(TRIM(elec_price_pps_kwh), '') AS DECIMAL(10,6)),
    CAST(NULLIF(TRIM(elec_price_tax_share_pct), '') AS DECIMAL(8,3)),

    CAST(NULLIF(TRIM(gas_price_eur_kwh), '') AS DECIMAL(10,6)),
    CAST(NULLIF(TRIM(gas_price_extax_eur_kwh), '') AS DECIMAL(10,6)),
    CAST(NULLIF(TRIM(gas_price_pps_kwh), '') AS DECIMAL(10,6)),
    CAST(NULLIF(TRIM(gas_price_tax_share_pct), '') AS DECIMAL(8,3)),

    CAST(NULLIF(TRIM(unable_warm_above60_pct), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(unable_warm_lowinc_pct), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(unable_warm_total_pct), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(unable_warm_income_gap_pp), '') AS DECIMAL(8,3)),

    CAST(NULLIF(TRIM(utility_arrears_above60_pct), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(utility_arrears_lowinc_pct), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(utility_arrears_total_pct), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(utility_arrears_income_gap_pp), '') AS DECIMAL(8,3)),

    TRIM(country_name),

    CASE LOWER(TRIM(is_eu27))
        WHEN 'true' THEN 1
        WHEN 'false' THEN 0
    END,

    CASE LOWER(TRIM(is_big6))
        WHEN 'true' THEN 1
        WHEN 'false' THEN 0
    END,

    CAST(NULLIF(TRIM(gas_fc_twh), '') AS DECIMAL(12,3)),
    CAST(NULLIF(TRIM(retailers_per_twh), '') AS DECIMAL(12,6)),

    CASE LOWER(TRIM(in_density_sample))
        WHEN 'true' THEN 1
        WHEN 'false' THEN 0
    END,

    CAST(NULLIF(TRIM(retailers_per_million), '') AS DECIMAL(12,6)),
    CAST(NULLIF(TRIM(e_cap_other_major_share), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(e_gen_other_major_share), '') AS DECIMAL(8,3)),
    CAST(NULLIF(TRIM(e_cap_gross_churn_mw), '') AS DECIMAL(12,3))

FROM germany_energiewende.master_panel_staging;

COMMIT;
