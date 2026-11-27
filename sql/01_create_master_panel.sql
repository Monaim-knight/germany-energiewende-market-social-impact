-- ============================================================
-- Germany's Energiewende (2013-2023)
-- MySQL Analytical Layer
-- Step 01: Create typed analytical table (master_panel)
--
-- Grain: one row per economy (geo) per calendar year (year)
-- Primary key: (geo, year)
-- Datatypes informed directly by R profiling (R/01_profile_and_validate_master_panel.R)
-- ============================================================

USE germany_energiewende;

CREATE TABLE IF NOT EXISTS master_panel (

    -- Identifiers
    geo                             CHAR(2) NOT NULL,
    year                            SMALLINT NOT NULL,

    -- Electricity market structure
    e_cap_connected_mw              DECIMAL(12,3),
    e_cap_decomm_mw                 DECIMAL(12,3),
    e_cap_net_var_mw                DECIMAL(12,3),
    e_cap_share                     DECIMAL(8,3),
    e_cap_top                       DECIMAL(8,3),
    e_gen_firms_ge5                 SMALLINT,
    e_gen_share                     DECIMAL(8,3),
    e_gen_top                       DECIMAL(8,3),
    elec_retailers                  SMALLINT,

    -- Gas market structure
    gas_retail_firms_ge5            SMALLINT,
    gas_retail_share_ge5            DECIMAL(8,3),
    gas_retailers                   SMALLINT,
    gas_upstream_firms              SMALLINT,

    -- Gas final consumption (GWh)
    fc_e_gwh                        DECIMAL(12,3),
    fc_ne_gwh                       DECIMAL(12,3),
    gas_fc_gwh                      DECIMAL(12,3),

    -- Population
    pop                             INT,

    -- Renewable energy shares (%)
    ren_total_pct                   DECIMAL(8,3),
    ren_elec_pct                    DECIMAL(8,3),

    -- Household electricity prices (EUR/PPS per kWh & tax share %)
    elec_price_eur_kwh              DECIMAL(10,6),
    elec_price_extax_eur_kwh        DECIMAL(10,6),
    elec_price_pps_kwh              DECIMAL(10,6),
    elec_price_tax_share_pct        DECIMAL(8,3),

    -- Household gas prices (EUR/PPS per kWh & tax share %)
    gas_price_eur_kwh               DECIMAL(10,6),
    gas_price_extax_eur_kwh         DECIMAL(10,6),
    gas_price_pps_kwh               DECIMAL(10,6),
    gas_price_tax_share_pct         DECIMAL(8,3),

    -- Energy poverty: inability to keep home adequately warm (%)
    unable_warm_above60_pct         DECIMAL(8,3),
    unable_warm_lowinc_pct          DECIMAL(8,3),
    unable_warm_total_pct           DECIMAL(8,3),
    unable_warm_income_gap_pp       DECIMAL(8,3),

    -- Energy poverty: arrears on utility bills (%)
    utility_arrears_above60_pct     DECIMAL(8,3),
    utility_arrears_lowinc_pct      DECIMAL(8,3),
    utility_arrears_total_pct       DECIMAL(8,3),
    utility_arrears_income_gap_pp   DECIMAL(8,3),

    -- Descriptive & cohort dimensions
    country_name                    VARCHAR(50) NOT NULL,
    is_eu27                         BOOLEAN NOT NULL,
    is_big6                         BOOLEAN NOT NULL,

    -- Derived gas-market measures
    gas_fc_twh                      DECIMAL(12,3),
    retailers_per_twh               DECIMAL(12,6),
    in_density_sample               BOOLEAN NOT NULL,
    retailers_per_million           DECIMAL(12,6),

    -- Derived electricity-market measures
    e_cap_other_major_share         DECIMAL(8,3),
    e_gen_other_major_share         DECIMAL(8,3),
    e_cap_gross_churn_mw            DECIMAL(12,3),

    -- Enforce validated country-year grain
    PRIMARY KEY (geo, year)
);
