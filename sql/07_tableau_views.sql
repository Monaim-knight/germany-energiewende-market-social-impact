-- ============================================================
-- Germany's Energiewende (2013-2023)
-- MySQL Analytical Layer
-- Step 07: Five Validated Presentation Views for Tableau
--
-- Architecture rule:
-- MySQL owns validated analytical logic (medians, ranks, endpoint deltas).
-- Tableau connects to these views strictly for visual presentation.
-- ============================================================

USE germany_energiewende;

-- ------------------------------------------------------------
-- View 1: Germany's structural transition (11 rows: 2013-2023)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW germany_energiewende.vw_tableau_de_transition AS
SELECT
    geo,
    country_name,
    year,
    ren_elec_pct,
    e_gen_share
FROM germany_energiewende.master_panel
WHERE geo = 'DE'
  AND year BETWEEN 2013 AND 2023;


-- ------------------------------------------------------------
-- View 2: 2023 concentration benchmark sensitivity (3 rows: All, EU-27, Big-6)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW germany_energiewende.vw_tableau_concentration_benchmark AS
WITH cohort_data AS (
    SELECT
        'All reporting economies' AS cohort,
        1 AS cohort_order,
        geo,
        e_gen_share
    FROM germany_energiewende.master_panel
    WHERE year = 2023
      AND e_gen_share IS NOT NULL

    UNION ALL

    SELECT
        'EU-27' AS cohort,
        2 AS cohort_order,
        geo,
        e_gen_share
    FROM germany_energiewende.master_panel
    WHERE year = 2023
      AND is_eu27 = 1
      AND e_gen_share IS NOT NULL

    UNION ALL

    SELECT
        'Big-6' AS cohort,
        3 AS cohort_order,
        geo,
        e_gen_share
    FROM germany_energiewende.master_panel
    WHERE year = 2023
      AND is_big6 = 1
      AND e_gen_share IS NOT NULL
),
ranked_cohorts AS (
    SELECT
        cohort,
        cohort_order,
        geo,
        e_gen_share,
        DENSE_RANK() OVER (
            PARTITION BY cohort
            ORDER BY e_gen_share DESC
        ) AS concentration_rank,
        ROW_NUMBER() OVER (
            PARTITION BY cohort
            ORDER BY e_gen_share
        ) AS ascending_row_number,
        COUNT(*) OVER (
            PARTITION BY cohort
        ) AS reporting_economies
    FROM cohort_data
),
cohort_medians AS (
    SELECT
        cohort,
        AVG(e_gen_share) AS cohort_median
    FROM ranked_cohorts
    WHERE ascending_row_number IN (
        FLOOR((reporting_economies + 1) / 2),
        FLOOR((reporting_economies + 2) / 2)
    )
    GROUP BY cohort
)
SELECT
    ranked.cohort,
    ranked.cohort_order,
    2023 AS benchmark_year,
    ranked.e_gen_share AS germany_e_gen_share,
    ranked.concentration_rank AS germany_rank,
    ranked.reporting_economies,
    ROUND(medians.cohort_median, 3) AS cohort_median,
    ROUND(ranked.e_gen_share - medians.cohort_median, 3) AS germany_vs_median_pp
FROM ranked_cohorts AS ranked
INNER JOIN cohort_medians AS medians
    ON ranked.cohort = medians.cohort
WHERE ranked.geo = 'DE';


-- ------------------------------------------------------------
-- View 3: Electricity affordability under stress, 2021-2023 (3 rows)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW germany_energiewende.vw_tableau_affordability_stress AS
WITH germany_price_endpoints AS (
    SELECT
        MAX(CASE WHEN year = 2021 THEN elec_price_eur_kwh END) AS final_price_2021,
        MAX(CASE WHEN year = 2023 THEN elec_price_eur_kwh END) AS final_price_2023,
        MAX(CASE WHEN year = 2021 THEN elec_price_extax_eur_kwh END) AS extax_price_2021,
        MAX(CASE WHEN year = 2023 THEN elec_price_extax_eur_kwh END) AS extax_price_2023,
        MAX(CASE WHEN year = 2021 THEN elec_price_tax_share_pct END) AS tax_share_2021,
        MAX(CASE WHEN year = 2023 THEN elec_price_tax_share_pct END) AS tax_share_2023
    FROM germany_energiewende.master_panel
    WHERE geo = 'DE'
      AND year IN (2021, 2023)
)
SELECT
    1 AS metric_order,
    'Final electricity price' AS metric,
    'Percent change' AS change_unit,
    final_price_2021 AS value_2021,
    final_price_2023 AS value_2023,
    ROUND(100.0 * (final_price_2023 - final_price_2021) / NULLIF(final_price_2021, 0), 2) AS change_value
FROM germany_price_endpoints

UNION ALL

SELECT
    2,
    'Ex-tax electricity price',
    'Percent change',
    extax_price_2021,
    extax_price_2023,
    ROUND(100.0 * (extax_price_2023 - extax_price_2021) / NULLIF(extax_price_2021, 0), 2)
FROM germany_price_endpoints

UNION ALL

SELECT
    3,
    'Tax share of final price',
    'Percentage-point change',
    tax_share_2021,
    tax_share_2023,
    ROUND(tax_share_2023 - tax_share_2021, 3)
FROM germany_price_endpoints;


-- ------------------------------------------------------------
-- View 4: Social resilience stress test, 2021-2023 (4 rows)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW germany_energiewende.vw_tableau_social_resilience AS
WITH social_endpoints AS (
    SELECT
        MAX(CASE WHEN year = 2021 THEN unable_warm_total_pct END) AS warm_total_2021,
        MAX(CASE WHEN year = 2023 THEN unable_warm_total_pct END) AS warm_total_2023,
        MAX(CASE WHEN year = 2021 THEN unable_warm_lowinc_pct END) AS warm_lowinc_2021,
        MAX(CASE WHEN year = 2023 THEN unable_warm_lowinc_pct END) AS warm_lowinc_2023,
        MAX(CASE WHEN year = 2021 THEN utility_arrears_total_pct END) AS arrears_total_2021,
        MAX(CASE WHEN year = 2023 THEN utility_arrears_total_pct END) AS arrears_total_2023,
        MAX(CASE WHEN year = 2021 THEN utility_arrears_lowinc_pct END) AS arrears_lowinc_2021,
        MAX(CASE WHEN year = 2023 THEN utility_arrears_lowinc_pct END) AS arrears_lowinc_2023
    FROM germany_energiewende.master_panel
    WHERE geo = 'DE'
      AND year IN (2021, 2023)
)
SELECT
    1 AS indicator_order,
    'Unable to keep home adequately warm' AS indicator,
    1 AS population_order,
    'Total population' AS population_group,
    warm_total_2021 AS value_2021,
    warm_total_2023 AS value_2023,
    ROUND(warm_total_2023 - warm_total_2021, 3) AS change_pp
FROM social_endpoints

UNION ALL

SELECT
    1,
    'Unable to keep home adequately warm',
    2,
    'Low income',
    warm_lowinc_2021,
    warm_lowinc_2023,
    ROUND(warm_lowinc_2023 - warm_lowinc_2021, 3)
FROM social_endpoints

UNION ALL

SELECT
    2,
    'Utility arrears',
    1,
    'Total population',
    arrears_total_2021,
    arrears_total_2023,
    ROUND(arrears_total_2023 - arrears_total_2021, 3)
FROM social_endpoints

UNION ALL

SELECT
    2,
    'Utility arrears',
    2,
    'Low income',
    arrears_lowinc_2021,
    arrears_lowinc_2023,
    ROUND(arrears_lowinc_2023 - arrears_lowinc_2021, 3)
FROM social_endpoints;


-- ------------------------------------------------------------
-- View 5: Gas-density analytical caution, 2021-2023 (3 rows)
-- ------------------------------------------------------------
CREATE OR REPLACE VIEW germany_energiewende.vw_tableau_gas_density_caution AS
WITH gas_endpoints AS (
    SELECT
        MAX(CASE WHEN year = 2021 THEN gas_retailers END) AS retailers_2021,
        MAX(CASE WHEN year = 2023 THEN gas_retailers END) AS retailers_2023,
        MAX(CASE WHEN year = 2021 THEN gas_fc_twh END) AS consumption_2021,
        MAX(CASE WHEN year = 2023 THEN gas_fc_twh END) AS consumption_2023,
        MAX(CASE WHEN year = 2021 THEN retailers_per_twh END) AS density_2021,
        MAX(CASE WHEN year = 2023 THEN retailers_per_twh END) AS density_2023
    FROM germany_energiewende.master_panel
    WHERE geo = 'DE'
      AND year IN (2021, 2023)
)
SELECT
    1 AS metric_order,
    'Gas retailers' AS metric,
    retailers_2021 AS value_2021,
    retailers_2023 AS value_2023,
    ROUND(100.0 * (retailers_2023 - retailers_2021) / NULLIF(retailers_2021, 0), 2) AS change_pct
FROM gas_endpoints

UNION ALL

SELECT
    2,
    'Gas consumption',
    consumption_2021,
    consumption_2023,
    ROUND(100.0 * (consumption_2023 - consumption_2021) / NULLIF(consumption_2021, 0), 2)
FROM gas_endpoints

UNION ALL

SELECT
    3,
    'Retailers per TWh',
    density_2021,
    density_2023,
    ROUND(100.0 * (density_2023 - density_2021) / NULLIF(density_2021, 0), 2)
FROM gas_endpoints;
