# Authoritative Data Codebook (Track A — Integrated Eurostat Suite)

This codebook defines every variable in `data/processed/master_panel.csv` (`396` country-years across `36` European economies, `2013–2023`). Exact API query URLs, retrieval timestamps, and SHA-256 file hashes are recorded in `data/manifest.json`.

---

## 1. Source Tables (8 Official Eurostat Sources)

| Source Key | Eurostat Code | Description | Frequency & Aggregation |
|---|---|---|---|
| `market_tsv` | `nrg_ind_market` | Electricity & natural gas market structure indicators (local extract `data/raw/estat_nrg_ind_market.tsv`) | Annual (`A`), 2013–2023 (2024 dropped due to sparse reporting) |
| `gas_final_consumption` | `nrg_bal_s` | Final natural gas consumption (`G3000`, `GWH`), computed as `FC_E + FC_NE` | Annual (`A`), sum of energy + non-energy final use |
| `population` | `demo_pjan` | Population on 1 January (`TOTAL`, sex `T`, `NR`) | Annual (`A`) |
| `renewables` | `nrg_ind_ren` | Renewable energy share overall (`REN`) and in electricity (`REN_ELC`, `PC`) | Annual (`A`), EU RED II methodology |
| `elec_prices` | `nrg_pc_204` | Household electricity prices, Band DC (`KWH2500-4999`, `E7000`, `KWH`, `I_TAX` & `X_TAX`, `EUR` & `PPS`) | Bi-annual (`S1`/`S2`) averaged to annual means |
| `gas_prices` | `nrg_pc_202` | Household natural gas prices, Band D2 (`GJ20-199`, `G3000`, `KWH`, `I_TAX` & `X_TAX`, `EUR` & `PPS`) | Bi-annual (`S1`/`S2`) averaged to annual means |
| `energy_poverty` | `ilc_mdes01` | EU-SILC: Inability to keep home adequately warm (`hhcomp=TOTAL`, `rskpovth` = `TOTAL`, `B_60`, `A_60`, `PC`) | Annual (`A`) |
| `utility_arrears` | `ilc_mdes07` | EU-SILC: Arrears on utility bills (`hhcomp=TOTAL`, `rskpovth` = `TOTAL`, `B_60`, `A_60`, `PC`) | Annual (`A`) |

---

## 2. Core Variables in `data/processed/master_panel.csv`

### Identifiers & Peer Cohorts
- `geo`: Eurostat two-letter country code. **Critical disambiguation:** `DE` = Germany, `EL` = Greece, `GE` = Georgia (never merged into Germany), `XK` = Kosovo.
- `year`: Integer `2013–2023`.
- `country_name`: Full English country name.
- `is_eu27`: Boolean flag for the 27 EU Member States.
- `is_big6`: Boolean flag for Europe's six largest interconnected markets (`DE, FR, IT, ES, PL, NL`).

### Pillar 1 — Electricity Market Structure & Transition
- `e_cap_share` (`CMPY_ECAP5`, `%`): Cumulative share of installed electricity capacity held by firms each holding ≥5%.
- `e_gen_share` (`CMPY_EG5`, `%`): Cumulative share of electricity generation held by firms each holding ≥5%.
- `e_cap_top` (`LCMPY_IECAP`, `%`): Capacity share of the single largest company.
- `e_gen_top` (`LCMPY_EG`, `%`): Generation share of the single largest company.
- `e_gen_firms_ge5` (`PCMPY_NEG5`, count): Number of companies producing ≥5% of electricity generation (Germany = `4` across 2013–2023).
- `e_cap_connected_mw` (`ECAP_CN`, `MW`): New electricity capacity connected in the year.
- `e_cap_decomm_mw` (`ECAP_DC`, `MW`): Electricity capacity decommissioned in the year.
- `e_cap_net_var_mw` (`ECAP_VAR`, `MW`): Net electricity capacity variation (`connected - decommissioned`).
- `ren_total_pct` (`REN`, `%`): Overall share of energy from renewable sources.
- `ren_elec_pct` (`REN_ELC`, `%`): Share of renewable electricity in gross final electricity consumption. *Domain note:* Under RED II, net hydro exporters (e.g., Norway) legitimately exceed `100%`.

### Pillar 2 — Natural Gas Market Structure & Decomposition
- `gas_retailers` (`GRTL`, count): Number of active natural gas retailers (Germany: `825` in 2013 → `995` in 2017 → `973` in 2023).
- `gas_fc_gwh` / `gas_fc_twh`: Final natural gas consumption (`FC_E + FC_NE`). Missing if either component is missing.
- `retailers_per_twh`: `gas_retailers / gas_fc_twh`.
- `in_density_sample`: Boolean screen (`gas_retailers` observed AND `gas_fc_gwh >= 1000` [1 TWh floor]).
- `retailers_per_million`: Robustness measure (`gas_retailers / (pop / 1e6)`) evaluated on `in_density_sample`.
- `gas_retail_share_ge5` (`GRTL_NG5`, `%`): Cumulative share of final gas sold by retailers each holding ≥5% of the market (cleaner competition indicator than raw count).
- `gas_retail_firms_ge5` (`GRTL_SELL_NG5`, count): Number of gas retailers selling ≥5% of total gas consumed.
- `gas_upstream_firms` (`CMPY_NG`, count): Number of companies bringing natural gas into the country.

### Pillar 3 — Household Affordability & Policy Tax Wedge
- `elec_price_eur_kwh`, `elec_price_pps_kwh`: Annual average household electricity price (Band DC, all taxes included) in EUR and Purchasing Power Standard (PPS) per kWh.
- `elec_price_extax_eur_kwh`: Ex-tax energy & network component (`X_TAX`, EUR/kWh).
- `elec_price_tax_share_pct`: Policy tax/levy share `= 100 * (all_tax - ex_tax) / all_tax`.
- `gas_price_eur_kwh`, `gas_price_pps_kwh`, `gas_price_extax_eur_kwh`, `gas_price_tax_share_pct`: Equivalent series for Band D2 household natural gas.

### Pillar 4 — Social Cohesion & Energy Poverty (EU-SILC)
- `unable_warm_total_pct`, `unable_warm_lowinc_pct` (`B_60`), `unable_warm_above60_pct` (`A_60`): Share of population unable to keep home adequately warm (`ilc_mdes01`).
- `unable_warm_income_gap_pp`: Distributional divide `= unable_warm_lowinc_pct - unable_warm_above60_pct`.
- `utility_arrears_total_pct`, `utility_arrears_lowinc_pct`, `utility_arrears_income_gap_pp`: Equivalent series for arrears on utility bills (`ilc_mdes07`).
- *Survey note:* Germany recorded a documented EU-SILC sampling/methodology break in 2020 (`unable_warm_total_pct` jumped temporarily to `7.0%`, then returned to `3.3%` in 2021). Crisis stress tests therefore use **2021** as the pre-shock baseline.

---

## 3. Retired Legacy v1 Labels (Withdrawn — Never Use)

| Retired v1 Label | Actual Eurostat Meaning |
|---|---|
| Electricity price competitiveness | `CMPY_ECAP5`: cumulative ≥5% electricity capacity share (`%`) |
| Gas price competitiveness | `CMPY_EG5`: cumulative ≥5% electricity generation share (`%`) |
| Energy price gap | Difference of two electricity shares (`CMPY_ECAP5 - CMPY_EG5`); retired |
| Grid infrastructure indicator | `GRTL`: raw count of natural gas retailers |
| Low-carbon electricity indicator | `LCMPY_IECAP`: largest firm's share of installed electricity capacity (`%`) |
