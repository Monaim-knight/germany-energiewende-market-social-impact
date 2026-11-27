-- ============================================================
-- Germany's Energiewende (2013-2023)
-- MySQL Analytical Layer
-- Step 02: Create all-TEXT staging table (master_panel_staging)
--
-- Why staging is required (observed direct-import failure):
-- Direct LOAD DATA into typed master_panel produced thousands of
-- warnings: blank numeric strings coerced to 0.000, True/False text
-- failed TINYINT/BOOLEAN conversion, and decimal-formatted counts
-- such as "4.0" failed direct integer casting.
-- Storing all 47 columns as raw TEXT preserves exact CSV values
-- for explicit, auditable conversion in Step 04.
-- ============================================================

USE germany_energiewende;

CREATE TABLE IF NOT EXISTS master_panel_staging (
    geo                             TEXT,
    year                            TEXT,

    e_cap_connected_mw              TEXT,
    e_cap_decomm_mw                 TEXT,
    e_cap_net_var_mw                TEXT,
    e_cap_share                     TEXT,
    e_cap_top                       TEXT,

    e_gen_firms_ge5                 TEXT,
    e_gen_share                     TEXT,
    e_gen_top                       TEXT,
    elec_retailers                  TEXT,

    gas_retail_firms_ge5            TEXT,
    gas_retail_share_ge5            TEXT,
    gas_retailers                   TEXT,
    gas_upstream_firms              TEXT,

    fc_e_gwh                        TEXT,
    fc_ne_gwh                       TEXT,
    gas_fc_gwh                      TEXT,
    pop                             TEXT,

    ren_total_pct                   TEXT,
    ren_elec_pct                    TEXT,

    elec_price_eur_kwh              TEXT,
    elec_price_extax_eur_kwh        TEXT,
    elec_price_pps_kwh              TEXT,
    elec_price_tax_share_pct        TEXT,

    gas_price_eur_kwh               TEXT,
    gas_price_extax_eur_kwh         TEXT,
    gas_price_pps_kwh               TEXT,
    gas_price_tax_share_pct         TEXT,

    unable_warm_above60_pct         TEXT,
    unable_warm_lowinc_pct          TEXT,
    unable_warm_total_pct           TEXT,
    unable_warm_income_gap_pp       TEXT,

    utility_arrears_above60_pct     TEXT,
    utility_arrears_lowinc_pct      TEXT,
    utility_arrears_total_pct       TEXT,
    utility_arrears_income_gap_pp   TEXT,

    country_name                    TEXT,
    is_eu27                         TEXT,
    is_big6                         TEXT,

    gas_fc_twh                      TEXT,
    retailers_per_twh               TEXT,
    in_density_sample               TEXT,
    retailers_per_million           TEXT,

    e_cap_other_major_share         TEXT,
    e_gen_other_major_share         TEXT,
    e_cap_gross_churn_mw            TEXT
);
