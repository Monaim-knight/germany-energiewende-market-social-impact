# Analytical Methodology

## 1. Selection of the Five Analytical Questions

Each of the five SQL queries targets a distinct decision question relevant to energy-market regulators, policy analysts, and BI stakeholders:

1. **Germany's Transition (2013–2023):** Separates the full decade into `2013–2019` (pre-pandemic/pre-crisis) and `2019–2023` (shock period) so long-run structural progress is not conflated with crisis-era affordability and hardship shifts.
2. **Concentration Benchmark Sensitivity (2023):** Tests whether Germany's generation concentration (`57.100%`) appears high or low across three peer cohorts—**All reporting economies (`N=35`)**, **EU-27 (`N=27`)**, and **Big-6 large interconnected markets (`N=6`)**.
3. **Gas-Retailer-Density Denominator Effect (2021–2023):** Decomposes `retailers_per_twh` into numerator (`gas_retailers`) and denominator (`gas_fc_twh`) to test whether rising density reflected genuine competitive entry or contracting consumption.
4. **Electricity-Price Decomposition (2021–2023):** Separates all-tax household electricity prices from the combined ex-tax component and policy tax share to explain why final bills rose even as taxes fell.
5. **Social-Resilience Stress Test (2021–2023):** Compares total-population vs. low-income (`<60%` median income) deterioration across thermal hardship (`ilc_mdes01`) and utility arrears (`ilc_mdes07`), computing direct `low-income − total` gaps from component series.

## 2. Why Medians & Multiple Peer Cohorts

- **Median over mean:** European market concentration distributions are heavily skewed by small island and non-EU single-utility systems (e.g., Cyprus `84.86%`, Kosovo `95.00%`, Malta `0.00%`). The cohort median resists extreme-value distortion.
- **Why peer-group choice changes the policy decision:**
  - *All reporting economies (`N=35`, median `63.355%`, DE rank `21/35`, `-6.255 pp`)* reflects broad pan-European reporting coverage.
  - *EU-27 2023 cross-section (`N=27`, median `59.440%`, DE rank `15/27`, `-2.340 pp`)* reflects EU regulatory membership. *(Note: The complementary Python time-series exhibit `outputs/tables/p1_balanced_eu27_e_gen_share.csv` restricts EU-27 to the `N=26` countries observed in all 11 years 2013–2023, yielding median `59.570%` and `-2.470 pp`. Both figures are valid for their respective scopes.)*
  - *Big-6 large markets (`N=6`, median `42.145%`, DE rank `2/6`, `+14.955 pp`)* benchmarks Germany against size-comparable interconnected European economies (`FR, DE, ES, PL, IT, NL`).

## 3. Why Ratios Must Be Decomposed & Why 2021–2023 Is the Stress Window

- **Ratio decomposition:** A ratio $R/C$ can rise sharply even when $R$ declines if $C$ contracts faster. Query 3 verifies this directly (`-0.61%` retailers vs. `-20.91%` consumption → `+25.66%` density), matching the Python pipeline's exact log-decomposition (`102.7%` denominator contribution).
- **2021–2023 stress window:** Captures the European energy-price shock while cleanly avoiding Germany's documented 2020 EU-SILC survey break (`unable_warm_total_pct` jumped temporarily to `7.0%` in 2020 before returning to `3.3%` in 2021).

## 4. Non-Causal Scope & Tool Separation

- **Non-causal design:** All five SQL queries and the Tableau dashboard are **strictly descriptive and benchmark-sensitive**. Co-movement between renewable expansion, market concentration, prices, and hardship does not establish causal treatment effects. *(Complementary two-way fixed effects panel associations in `src/energiewende/analytics.py` are likewise non-causal and strictly screened by a 100% leave-one-out stability gate.)*
- **Separation of responsibilities:**
  - **Python (`src/energiewende/`):** Eurostat API ingestion, SHA-256 provenance logging, panel construction, automated test contracts, and supplementary econometrics/web explorer.
  - **R (`R/01_profile_and_validate_master_panel.R`):** Independent, risk-driven grain, identifier, and datatype profiling prior to relational modeling.
  - **MySQL (`sql/00`–`sql/07`):** Controlled staging ingestion, primary-key enforcement, validated analytical queries, and presentation views (`vw_tableau_*`).
  - **Tableau (`tableau/`, `assets/energiewende_executive_dashboard.png`):** Single executive dashboard dedicated strictly to decision communication—never recalculating MySQL medians or ranks independently.
