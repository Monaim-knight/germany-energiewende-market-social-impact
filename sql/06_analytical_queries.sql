-- ============================================================
-- Germany's Energiewende (2013-2023)
-- MySQL Analytical Layer
-- Step 06: Five Completed Analytical SQL Queries
--
-- Note: All outputs are descriptive and benchmark-sensitive.
-- Co-movement does not establish causality.
-- ============================================================

USE germany_energiewende;

-- ============================================================
-- QUERY 1: Germany's Transition, 2013-2023
-- Question: How did Germany's renewable electricity, electricity-
-- generation concentration, household electricity price, and
-- thermal energy poverty evolve from 2013 to 2023?
-- ============================================================

-- 1a. Annual German trajectory
SELECT
    year,
    ren_elec_pct,
    e_gen_share,
    elec_price_eur_kwh,
    unable_warm_total_pct
FROM germany_energiewende.master_panel
WHERE geo = 'DE'
ORDER BY year;

-- 1b. Decision-relevant period changes (2013-2023, 2013-2019, 2019-2023)
WITH germany_period_values AS (
    SELECT
        MAX(CASE WHEN year = 2013 THEN ren_elec_pct END) AS ren_2013,
        MAX(CASE WHEN year = 2019 THEN ren_elec_pct END) AS ren_2019,
        MAX(CASE WHEN year = 2023 THEN ren_elec_pct END) AS ren_2023,

        MAX(CASE WHEN year = 2013 THEN e_gen_share END) AS concentration_2013,
        MAX(CASE WHEN year = 2019 THEN e_gen_share END) AS concentration_2019,
        MAX(CASE WHEN year = 2023 THEN e_gen_share END) AS concentration_2023,

        MAX(CASE WHEN year = 2013 THEN elec_price_eur_kwh END) AS price_2013,
        MAX(CASE WHEN year = 2019 THEN elec_price_eur_kwh END) AS price_2019,
        MAX(CASE WHEN year = 2023 THEN elec_price_eur_kwh END) AS price_2023,

        MAX(CASE WHEN year = 2013 THEN unable_warm_total_pct END) AS poverty_2013,
        MAX(CASE WHEN year = 2019 THEN unable_warm_total_pct END) AS poverty_2019,
        MAX(CASE WHEN year = 2023 THEN unable_warm_total_pct END) AS poverty_2023
    FROM germany_energiewende.master_panel
    WHERE geo = 'DE'
)
SELECT
    '2013-2023' AS comparison_period,
    ROUND(ren_2023 - ren_2013, 3) AS renewable_change_pp,
    ROUND(concentration_2023 - concentration_2013, 3) AS concentration_change_pp,
    ROUND(100.0 * (price_2023 - price_2013) / NULLIF(price_2013, 0), 2) AS electricity_price_change_pct,
    ROUND(poverty_2023 - poverty_2013, 3) AS unable_warm_change_pp
FROM germany_period_values

UNION ALL

SELECT
    '2013-2019',
    ROUND(ren_2019 - ren_2013, 3),
    ROUND(concentration_2019 - concentration_2013, 3),
    ROUND(100.0 * (price_2019 - price_2013) / NULLIF(price_2013, 0), 2),
    ROUND(poverty_2019 - poverty_2013, 3)
FROM germany_period_values

UNION ALL

SELECT
    '2019-2023',
    ROUND(ren_2023 - ren_2019, 3),
    ROUND(concentration_2023 - concentration_2019, 3),
    ROUND(100.0 * (price_2023 - price_2019) / NULLIF(price_2019, 0), 2),
    ROUND(poverty_2023 - poverty_2019, 3)
FROM germany_period_values;


-- ============================================================
-- QUERY 2: Concentration Benchmark Sensitivity (2023)
-- Question: Is Germany's 2023 electricity-generation concentration
-- high or low relative to appropriate European peer groups?
-- ============================================================

-- 2a. Full 2023 reporting distribution (35 economies)
SELECT
    geo,
    country_name,
    e_gen_share,
    is_eu27,
    is_big6
FROM germany_energiewende.master_panel
WHERE year = 2023
  AND e_gen_share IS NOT NULL
ORDER BY e_gen_share DESC;

-- 2b. Germany's rank and distance to median across All (N=35), EU-27 (N=27), and Big-6 (N=6)
WITH cohort_data AS (
    SELECT
        'All reporting economies' AS cohort,
        geo,
        country_name,
        e_gen_share
    FROM germany_energiewende.master_panel
    WHERE year = 2023
      AND e_gen_share IS NOT NULL

    UNION ALL

    SELECT
        'EU-27' AS cohort,
        geo,
        country_name,
        e_gen_share
    FROM germany_energiewende.master_panel
    WHERE year = 2023
      AND is_eu27 = 1
      AND e_gen_share IS NOT NULL

    UNION ALL

    SELECT
        'Big-6' AS cohort,
        geo,
        country_name,
        e_gen_share
    FROM germany_energiewende.master_panel
    WHERE year = 2023
      AND is_big6 = 1
      AND e_gen_share IS NOT NULL
),
ranked_cohorts AS (
    SELECT
        cohort,
        geo,
        country_name,
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
    ranked.e_gen_share AS germany_e_gen_share,
    ranked.concentration_rank AS germany_rank,
    ranked.reporting_economies,
    ROUND(medians.cohort_median, 3) AS cohort_median,
    ROUND(ranked.e_gen_share - medians.cohort_median, 3) AS germany_vs_median_pp
FROM ranked_cohorts AS ranked
INNER JOIN cohort_medians AS medians
    ON ranked.cohort = medians.cohort
WHERE ranked.geo = 'DE'
ORDER BY
    CASE ranked.cohort
        WHEN 'All reporting economies' THEN 1
        WHEN 'EU-27' THEN 2
        WHEN 'Big-6' THEN 3
    END;


-- ============================================================
-- QUERY 3: Gas-Retailer-Density Denominator Effect (2021-2023)
-- Question: Did Germany's increase in gas retailers per TWh
-- reflect retailer entry, or primarily declining gas consumption?
-- ============================================================

-- 3a. Endpoint inspection
SELECT
    year,
    gas_retailers,
    gas_fc_twh,
    retailers_per_twh
FROM germany_energiewende.master_panel
WHERE geo = 'DE'
  AND year IN (2021, 2023)
ORDER BY year;

-- 3b. Component percentage changes
WITH germany_gas_endpoints AS (
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
    retailers_2021,
    retailers_2023,
    ROUND(100.0 * (retailers_2023 - retailers_2021) / NULLIF(retailers_2021, 0), 2) AS retailer_count_change_pct,
    consumption_2021,
    consumption_2023,
    ROUND(100.0 * (consumption_2023 - consumption_2021) / NULLIF(consumption_2021, 0), 2) AS gas_consumption_change_pct,
    density_2021,
    density_2023,
    ROUND(100.0 * (density_2023 - density_2021) / NULLIF(density_2021, 0), 2) AS retailer_density_change_pct
FROM germany_gas_endpoints;


-- ============================================================
-- QUERY 4: Electricity-Price Decomposition (2021-2023)
-- Question: Why did Germany's household electricity price rise
-- while the tax share declined?
-- ============================================================

-- 4a. Full German price and tax-share trajectory
SELECT
    year,
    elec_price_eur_kwh,
    elec_price_extax_eur_kwh,
    elec_price_tax_share_pct
FROM germany_energiewende.master_panel
WHERE geo = 'DE'
ORDER BY year;

-- 4b. 2021-2023 decomposition
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
    final_price_2021,
    final_price_2023,
    ROUND(100.0 * (final_price_2023 - final_price_2021) / NULLIF(final_price_2021, 0), 2) AS final_price_change_pct,
    extax_price_2021,
    extax_price_2023,
    ROUND(100.0 * (extax_price_2023 - extax_price_2021) / NULLIF(extax_price_2021, 0), 2) AS extax_price_change_pct,
    tax_share_2021,
    tax_share_2023,
    ROUND(tax_share_2023 - tax_share_2021, 3) AS tax_share_change_pp
FROM germany_price_endpoints;


-- ============================================================
-- QUERY 5: Social-Resilience Stress Test (2021-2023)
-- Question: During 2021-2023, did household energy stress worsen
-- more for low-income households than for the total population?
--
-- Metric note: Stored unable_warm_income_gap_pp and
-- utility_arrears_income_gap_pp equal (B_60 low-income - A_60 above-60%).
-- Below we compute direct (low-income - total population) gaps from
-- the component series to match this policy question exactly.
-- ============================================================

-- 5a. Annual inspection (2021-2023)
SELECT
    year,
    unable_warm_total_pct,
    unable_warm_lowinc_pct,
    unable_warm_income_gap_pp,
    utility_arrears_total_pct,
    utility_arrears_lowinc_pct,
    utility_arrears_income_gap_pp
FROM germany_energiewende.master_panel
WHERE geo = 'DE'
  AND year IN (2021, 2022, 2023)
ORDER BY year;

-- 5b. Direct 2021-2023 changes and low-income vs. total gaps
WITH germany_social_endpoints AS (
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
    ROUND(warm_total_2023 - warm_total_2021, 3) AS warm_total_change_pp,
    ROUND(warm_lowinc_2023 - warm_lowinc_2021, 3) AS warm_lowinc_change_pp,
    ROUND(warm_lowinc_2021 - warm_total_2021, 3) AS warm_gap_2021_pp,
    ROUND(warm_lowinc_2023 - warm_total_2023, 3) AS warm_gap_2023_pp,
    ROUND(arrears_total_2023 - arrears_total_2021, 3) AS arrears_total_change_pp,
    ROUND(arrears_lowinc_2023 - arrears_lowinc_2021, 3) AS arrears_lowinc_change_pp,
    ROUND(arrears_lowinc_2021 - arrears_total_2021, 3) AS arrears_gap_2021_pp,
    ROUND(arrears_lowinc_2023 - arrears_total_2023, 3) AS arrears_gap_2023_pp
FROM germany_social_endpoints;
