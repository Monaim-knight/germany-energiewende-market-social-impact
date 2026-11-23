# Pipeline Analytical Results (Track A — Integrated Suite)

Generated automatically by `python -m energiewende.pipeline`. Do not edit by hand.

## Pillar 1: Electricity Transition & Peer-Cohort Sensitivity (2013–2023)

- **Germany renewable electricity (`nrg_ind_ren`, `REN_ELC`):** rose from **25.3%** (2013) to **51.9%** (2023) (**+26.7 pp**), accompanied by **22.8 GW** of new capacity connected in 2023 and **11.1 GW** decommissioned in 2021.
- **Germany generation concentration (`CMPY_EG5`):** fell from **74.0%** to **57.1%** (**-16.9 pp**); capacity concentration (`CMPY_ECAP5`) fell from **67.0%** to **52.5%**.
- **Benchmark cohort effect (2023 `CMPY_EG5`):**
  - All reporters (unbalanced, N=35): Germany is **-6.3 pp** vs. median (63.4%), rank **21 of 35**.
  - Balanced EU-27 (constant N=26): Germany is **-2.5 pp** vs. median (59.6%), rank **15 of 26**.
  - Big-6 large markets (`DE, FR, IT, ES, PL, NL`): Germany is **+15.0 pp ABOVE** the Big-6 median (42.1%), rank **2 of 6** (behind only France).

## Pillar 2: Gas Market Structure & Exact Ratio Log-Decomposition

- **Full decade (2013–2023):** Germany's gas-retailer density rose **+37.3%** (`1.28 → 1.76` retailers/TWh): **52.1%** from retailer entry (`825 → 973`) and **47.9%** from declining gas demand (`642.6 → 552.2 TWh`).
- **2021–2023 Energy Crisis Artifact:** Retailer density jumped **+25.7%** (`1.40 → 1.76`), even though retailer count **fell -0.6%** (`979 → 973`). Exactly **102.7%** of the log jump was driven by the **-20.9%** collapse in German final gas consumption (`698.2 → 552.2 TWh`).
- **True gas retail concentration (`GRTL_NG5`):** Cumulative share of retailers holding ≥5% fell in half from **26.0%** (2013) to **13.3%** (2023) — rank **6 of 6** (least concentrated) in the Big-6 vs. Big-6 median **70.1%**.

## Pillar 3: Household Affordability & Policy Tax-Wedge Regime Shift

- **Electricity (`nrg_pc_204`, Band DC):** Germany's all-tax price rose from **€0.321/kWh** (2021) to **€0.407/kWh** (2023, `0.364 PPS/kWh` — highest nominal price in the Big-6).
- **Tax-wedge shift:** Abolishing the EEG surcharge cut Germany's electricity tax share from **50.9%** (2021) to **28.1%** (2023), yet ex-tax energy/network costs surged **+85.4%** (`€0.158 → €0.293/kWh`).
- **Natural gas (`nrg_pc_202`, Band D2):** Germany's household gas price rose **+77.4%** (`€0.067 → €0.119/kWh`) while the tax wedge dropped from **32.1%** to **20.0%**.

## Pillar 4: Social Cohesion & Energy-Poverty Stress Test (`ilc_mdes01`, `ilc_mdes07`)

- **Germany inability to keep home adequately warm (Total):** rose from **3.3%** (2021, rank 17 of 27 in EU-27) to **8.2%** (2023, rank **10 of 27**), crossing **above** the EU-27 median (**7.1%**).
- **Low-income distributional divide (`<60%` median income):** rose from **7.8%** (2021) to **14.3%** (2023) — a **+7.1 pp** gap vs. higher-income households (`7.2%`), though still lower in absolute level than Spain (34.3%), France (25.1%), Italy (21.6%), and the Netherlands (21.6%).
- **Utility arrears (`ilc_mdes07`):** rose from **3.7%** to **5.4%** overall, and from **6.5%** to **9.3%** among low-income households.

## Panel Econometrics (Two-Way FE + Country-Clustered SEs + Strict LOO Gate)

| Model | Coef | SE | p-value | 95% CI | Within R² | N (Countries) | LOO <=50% | Gate |
|---|---:|---:|---:|---|---:|---:|---:|---|
| m1_ren_to_deconc_all | -0.5330 | 0.2018 | 0.008 | [-0.9285, -0.1376] | 0.071 | 359 (34) | 34/34 | **PASS** |
| m2_ren_to_deconc_eu27 | -0.5390 | 0.2528 | 0.033 | [-1.0344, -0.0435] | 0.064 | 291 (27) | 27/27 | **PASS** |
| m3_conc_to_elec_pps | 0.0007 | 0.0003 | 0.024 | [0.0001, 0.0013] | 0.032 | 291 (27) | 27/27 | **PASS** |
| m4_elec_pps_to_warm_all | 8.9166 | 11.4073 | 0.434 | [-13.4412, 31.2744] | 0.008 | 297 (27) | 25/27 | FAIL |
| m5_gas_pps_to_warm_lowinc | 32.6051 | 32.8292 | 0.321 | [-31.7390, 96.9492] | 0.012 | 264 (24) | 22/24 | FAIL |
| m6_conc_to_warm_total | 0.0240 | 0.0435 | 0.581 | [-0.0612, 0.1092] | 0.004 | 291 (27) | 24/27 | FAIL |
| m7_legacy_rq3_density | 0.0026 | 0.0101 | 0.799 | [-0.0172, 0.0223] | 0.001 | 326 (30) | 25/30 | FAIL |

### Econometric Interpretation (Non-Causal Associations)

- **Passing strict gate (M1–M3):** Within-country renewable electricity expansion associates strongly with lower generation concentration (`-0.533` pp per +1 pp renewable share, 34/34 LOO), and higher generation concentration associates with modestly higher PPS household electricity prices (`+0.0007` PPS/kWh per +1 pp share, 27/27 LOO).
- **Failing strict gate (M4–M7):** Direct within-country links from market structure or prices to thermal energy poverty do **not** pass the strict LOO/CI gate—confirming that national fiscal buffers, housing efficiency, and social policy mediate whether price shocks translate into household deprivation.
