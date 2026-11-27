# Data Dictionary — `master_panel` (47 Columns)

**Grain:** One row per European economy (`geo`) per calendar year (`year`), `2013–2023` (`396` rows, `36` economies, composite primary key `(geo, year)`).  
**Column-role summary:** `2` keys, `1` descriptive dimension, `3` cohort/eligibility dimensions, `33` base/input measures, `8` derived panel measures.

| # | Column | Analytical Meaning | Unit | Role | MySQL Type | Nullable | Lineage / Formula | Known Caveats |
|---:|---|---|---|---|---|---|---|---|
| 1 | `geo` | Eurostat 2-letter country code | Code | Key | `CHAR(2)` | NO | Base (`nrg_ind_market`) | `EL` = Greece, `GE` = Georgia (never merged into `DE`), `XK` = Kosovo |
| 2 | `year` | Calendar year (`2013–2023`) | Year | Key | `SMALLINT` | NO | Base | 2024 excluded due to sparse reporting |
| 3 | `e_cap_connected_mw` | New electricity capacity connected | MW | Base/input measure | `DECIMAL(12,3)` | YES | `nrg_ind_market` (`ECAP_CN`) | Voluntary Eurostat reporting; blanks = SQL `NULL` |
| 4 | `e_cap_decomm_mw` | Electricity capacity decommissioned | MW | Base/input measure | `DECIMAL(12,3)` | YES | `nrg_ind_market` (`ECAP_DC`) | Blanks = unavailable or confidential |
| 5 | `e_cap_net_var_mw` | Net electricity capacity variation | MW | Base/input measure | `DECIMAL(12,3)` | YES | `nrg_ind_market` (`ECAP_VAR`) | Legitimately negative in net-retirement years |
| 6 | `e_cap_share` | Cumulative capacity share of firms with ≥5% | % | Base/input measure | `DECIMAL(8,3)` | YES | `nrg_ind_market` (`CMPY_ECAP5`) | `0–100` share; not a price indicator |
| 7 | `e_cap_top` | Capacity share of the single largest company | % | Base/input measure | `DECIMAL(8,3)` | YES | `nrg_ind_market` (`LCMPY_IECAP`) | `NULL` for AT, NL, TR, NO (unreported) |
| 8 | `e_gen_firms_ge5` | Count of companies producing ≥5% of generation | Count | Base/input measure | `SMALLINT` | YES | `nrg_ind_market` (`PCMPY_NEG5`) | Stored as float-string `"4.0"` in CSV; two-stage cast in MySQL |
| 9 | `e_gen_share` | Cumulative generation share of firms with ≥5% | % | Base/input measure | `DECIMAL(8,3)` | YES | `nrg_ind_market` (`CMPY_EG5`) | Core Query 1 & Query 2 metric; 35 reporting economies in 2023 |
| 10 | `e_gen_top` | Generation share of the single largest company | % | Base/input measure | `DECIMAL(8,3)` | YES | `nrg_ind_market` (`LCMPY_EG`) | `NULL` for AT, NL, TR, NO |
| 11 | `elec_retailers` | Number of active electricity retailers | Count | Base/input measure | `SMALLINT` | YES | `nrg_ind_market` (`ERTL`) | Raw count reflects market size and regional utility structure |
| 12 | `gas_retail_firms_ge5` | Gas retailers selling ≥5% of total gas consumed | Count | Base/input measure | `SMALLINT` | YES | `nrg_ind_market` (`GRTL_SELL_NG5`) | Whole-number count |
| 13 | `gas_retail_share_ge5` | Cumulative share of gas retailers with ≥5% | % | Base/input measure | `DECIMAL(8,3)` | YES | `nrg_ind_market` (`GRTL_NG5`) | Share-based gas retail concentration indicator |
| 14 | `gas_retailers` | Number of active natural gas retailers | Count | Base/input measure | `SMALLINT` | YES | `nrg_ind_market` (`GRTL`) | Numerator for `retailers_per_twh`; not a grid metric |
| 15 | `gas_upstream_firms` | Companies bringing natural gas into country | Count | Base/input measure | `SMALLINT` | YES | `nrg_ind_market` (`CMPY_NG`) | Wholesale/import shippers, not retail suppliers |
| 16 | `fc_e_gwh` | Final natural gas consumption — energy use | GWh | Base/input measure | `DECIMAL(12,3)` | YES | `nrg_bal_s` (`FC_E`, `G3000`) | Component of `gas_fc_gwh` |
| 17 | `fc_ne_gwh` | Final natural gas consumption — non-energy use | GWh | Base/input measure | `DECIMAL(12,3)` | YES | `nrg_bal_s` (`FC_NE`, `G3000`) | Component of `gas_fc_gwh` |
| 18 | `gas_fc_gwh` | Total final natural gas consumption | GWh | Base/input measure | `DECIMAL(12,3)` | YES | `fc_e_gwh + fc_ne_gwh` (pre-panel) | `NULL` if either component is missing |
| 19 | `pop` | Total population on 1 January | Persons | Base/input measure | `INT` | YES | `demo_pjan` (`TOTAL`, sex `T`) | DE 2013 unit-check anchor = `80,523,746` |
| 20 | `ren_total_pct` | Overall share of energy from renewables | % | Base/input measure | `DECIMAL(8,3)` | YES | `nrg_ind_ren` (`REN`) | Eurostat RED II methodology |
| 21 | `ren_elec_pct` | Renewable share in gross electricity consumption | % | Base/input measure | `DECIMAL(8,3)` | YES | `nrg_ind_ren` (`REN_ELC`) | Can legitimately exceed `100%` in net hydro exporters (e.g., Norway ~120%); no 0–100 constraint applied |
| 22 | `elec_price_eur_kwh` | Household electricity price, all taxes (Band DC) | EUR/kWh | Base/input measure | `DECIMAL(10,6)` | YES | `nrg_pc_204` (`I_TAX`, `EUR`, S1/S2 avg) | Band DC = `2,500–4,999 kWh/yr` |
| 23 | `elec_price_extax_eur_kwh` | Household electricity price, excluding taxes/levies | EUR/kWh | Base/input measure | `DECIMAL(10,6)` | YES | `nrg_pc_204` (`X_TAX`, `EUR`, S1/S2 avg) | Combined ex-tax component (not split into wholesale/network/margin) |
| 24 | `elec_price_pps_kwh` | Household electricity price in PPS, all taxes | PPS/kWh | Base/input measure | `DECIMAL(10,6)` | YES | `nrg_pc_204` (`I_TAX`, `PPS`, S1/S2 avg) | Purchasing Power Standard adjustment |
| 25 | `elec_price_tax_share_pct` | Taxes & levies share of final electricity price | % | Base/input measure | `DECIMAL(8,3)` | YES | `100 * (all_tax - ex_tax) / all_tax` (pre-panel) | Legitimately negative in 2022–2023 when subsidies exceeded taxes (AT, EL, IE, LU) |
| 26 | `gas_price_eur_kwh` | Household gas price, all taxes (Band D2) | EUR/kWh | Base/input measure | `DECIMAL(10,6)` | YES | `nrg_pc_202` (`I_TAX`, `EUR`, S1/S2 avg) | Band D2 = `20–199 GJ/yr` |
| 27 | `gas_price_extax_eur_kwh` | Household gas price, excluding taxes/levies | EUR/kWh | Base/input measure | `DECIMAL(10,6)` | YES | `nrg_pc_202` (`X_TAX`, `EUR`, S1/S2 avg) | Combined ex-tax component |
| 28 | `gas_price_pps_kwh` | Household gas price in PPS, all taxes | PPS/kWh | Base/input measure | `DECIMAL(10,6)` | YES | `nrg_pc_202` (`I_TAX`, `PPS`, S1/S2 avg) | Purchasing Power Standard adjustment |
| 29 | `gas_price_tax_share_pct` | Taxes & levies share of final gas price | % | Base/input measure | `DECIMAL(8,3)` | YES | `100 * (all_tax - ex_tax) / all_tax` (pre-panel) | Can be negative under net household gas subsidies |
| 30 | `unable_warm_above60_pct` | Unable to keep home warm — ≥60% median income | % | Base/input measure | `DECIMAL(8,3)` | YES | `ilc_mdes01` (`rskpovth=A_60`) | EU-SILC survey; DE had a 2020 survey break |
| 31 | `unable_warm_lowinc_pct` | Unable to keep home warm — <60% median income | % | Base/input measure | `DECIMAL(8,3)` | YES | `ilc_mdes01` (`rskpovth=B_60`) | Core Query 5 low-income metric |
| 32 | `unable_warm_total_pct` | Unable to keep home warm — total population | % | Base/input measure | `DECIMAL(8,3)` | YES | `ilc_mdes01` (`rskpovth=TOTAL`) | Core Query 1 & Query 5 total metric |
| 33 | `unable_warm_income_gap_pp` | Stored thermal hardship gap (`B_60 − A_60`) | pp | Derived measure | `DECIMAL(8,3)` | YES | `unable_warm_lowinc_pct - unable_warm_above60_pct` | **Caveat:** Compares `<60%` vs `≥60%` (not vs `TOTAL`). Query 5 computes `lowinc − total` directly. |
| 34 | `utility_arrears_above60_pct` | Utility bill arrears — ≥60% median income | % | Base/input measure | `DECIMAL(8,3)` | YES | `ilc_mdes07` (`rskpovth=A_60`) | EU-SILC survey |
| 35 | `utility_arrears_lowinc_pct` | Utility bill arrears — <60% median income | % | Base/input measure | `DECIMAL(8,3)` | YES | `ilc_mdes07` (`rskpovth=B_60`) | Core Query 5 low-income metric |
| 36 | `utility_arrears_total_pct` | Utility bill arrears — total population | % | Base/input measure | `DECIMAL(8,3)` | YES | `ilc_mdes07` (`rskpovth=TOTAL`) | Core Query 5 total metric |
| 37 | `utility_arrears_income_gap_pp` | Stored utility arrears gap (`B_60 − A_60`) | pp | Derived measure | `DECIMAL(8,3)` | YES | `utility_arrears_lowinc_pct - utility_arrears_above60_pct` | **Caveat:** Compares `<60%` vs `≥60%`; legitimately negative where `A_60 > B_60` (`ME 2013`, `MT 2023`). Query 5 computes `lowinc − total` directly. |
| 38 | `country_name` | English economy name | Text | Descriptive dimension | `VARCHAR(50)` | NO | Mapped from `geo` in `config.py` | Verified 1-to-1 bijection with `geo` (`36` values) |
| 39 | `is_eu27` | EU-27 member state flag | Flag (`0/1`) | Cohort/eligibility dimension | `BOOLEAN` (`TINYINT(1)`) | NO | Static cohort definition (`config.py`) | Stable within every economy across all 11 years |
| 40 | `is_big6` | Big-6 large market flag (`DE,FR,IT,ES,PL,NL`) | Flag (`0/1`) | Cohort/eligibility dimension | `BOOLEAN` (`TINYINT(1)`) | NO | Static cohort definition (`config.py`) | Stable within every economy across all 11 years |
| 41 | `gas_fc_twh` | Total final natural gas consumption in TWh | TWh | Derived measure | `DECIMAL(12,3)` | YES | `gas_fc_gwh / 1000.0` | Denominator for `retailers_per_twh` |
| 42 | `retailers_per_twh` | Gas retailers per TWh of final consumption | Count/TWh | Derived measure | `DECIMAL(12,6)` | YES | `gas_retailers / gas_fc_twh` | Sensitive to consumption contractions (Query 3) |
| 43 | `in_density_sample` | Eligibility flag for density ranking | Flag (`0/1`) | Cohort/eligibility dimension | `BOOLEAN` (`TINYINT(1)`) | NO | `gas_retailers IS NOT NULL AND gas_fc_gwh >= 1000` | Excludes micro-markets below 1 TWh |
| 44 | `retailers_per_million` | Gas retailers per million inhabitants | Count/M | Derived measure | `DECIMAL(12,6)` | YES | `gas_retailers / (pop / 1e6)` where `in_density_sample = 1` | Robustness denominator only |
| 45 | `e_cap_other_major_share` | Cumulative ≥5% capacity share excluding top firm | % | Derived measure | `DECIMAL(8,3)` | YES | `e_cap_share - e_cap_top` | `NULL` if either input is `NULL` |
| 46 | `e_gen_other_major_share` | Cumulative ≥5% generation share excluding top firm | % | Derived measure | `DECIMAL(8,3)` | YES | `e_gen_share - e_gen_top` | `NULL` if either input is `NULL` |
| 47 | `e_cap_gross_churn_mw` | Gross annual electricity capacity turnover | MW | Derived measure | `DECIMAL(12,3)` | YES | `e_cap_connected_mw + e_cap_decomm_mw` | Measures combined entry + retirement volume |
