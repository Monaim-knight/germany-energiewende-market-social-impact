"""Core analytical computations for all four Track A pillars.

Pillar 1: Electricity transition & concentration (All reporters vs Balanced EU-27 vs Big-6)
Pillar 2: Gas market structure & exact log-decomposition of retailer density
Pillar 3: Household affordability & tax-wedge regime shift (EUR & PPS)
Pillar 4: Social cohesion & energy-poverty stress test + TWFE models with LOO gates
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from energiewende.config import (
    DENSITY_FLAT_REL,
    GAS_FLOOR_GWH,
    LOO_BAND,
    MIN_YEARS_FOR_FE,
    SHARE_FLAT_PP,
    YEAR_MAX,
    YEAR_MIN,
)


def yearly_distribution(frame: pd.DataFrame, column: str, ref_geo: str = "DE") -> pd.DataFrame:
    """Compute annual median, IQR, reference-country value, gap to median, and descending rank."""
    rows = []
    for year, grp in frame.dropna(subset=[column]).groupby("year"):
        vals = grp[column].astype(float)
        ref = grp.loc[grp["geo"] == ref_geo, column]
        ref_val = float(ref.iloc[0]) if len(ref) else np.nan
        ranks = vals.rank(ascending=False, method="min")
        ref_rank = float(ranks.loc[ref.index].iloc[0]) if len(ref) else np.nan
        med = float(vals.median())
        rows.append(
            {
                "year": int(year),
                "de": ref_val,
                "median": med,
                "mean": float(vals.mean()),
                "p25": float(vals.quantile(0.25)),
                "p75": float(vals.quantile(0.75)),
                "de_minus_median": ref_val - med if pd.notna(ref_val) else np.nan,
                "de_rank": ref_rank,
                "n": int(len(vals)),
            }
        )
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def balanced_cohort(frame: pd.DataFrame, column: str, eu27_only: bool = True) -> pd.DataFrame:
    """Restrict to countries observed in every year of [YEAR_MIN, YEAR_MAX] for a given column."""
    sub = frame[frame["is_eu27"]].copy() if eu27_only else frame.copy()
    sub = sub.dropna(subset=[column])
    expected_years = YEAR_MAX - YEAR_MIN + 1
    counts = sub.groupby("geo")["year"].nunique()
    balanced_geos = counts[counts == expected_years].index
    return sub[sub["geo"].isin(balanced_geos)].copy()


def decompose_retailer_density(panel: pd.DataFrame, geo: str = "DE") -> pd.DataFrame:
    """Exact log-decomposition of gas-retailer density across key periods.

    Identity: d_ln(R / C) = d_ln(R) - d_ln(C)
      - numerator_contrib   = ln(R_t1 / R_t0)
      - denominator_contrib = -ln(C_t1 / C_t0)
      - total_log_change    = ln(D_t1 / D_t0) == numerator_contrib + denominator_contrib
    """
    sub = panel[panel["geo"] == geo].set_index("year")
    periods = [
        ("Full decade (2013-2023)", 2013, 2023),
        ("Entry expansion (2013-2017)", 2013, 2017),
        ("Pre-crisis plateau (2017-2021)", 2017, 2021),
        ("Energy crisis shock (2021-2023)", 2021, 2023),
    ]
    rows = []
    for label, y0, y1 in periods:
        r0, r1 = float(sub.loc[y0, "gas_retailers"]), float(sub.loc[y1, "gas_retailers"])
        c0, c1 = float(sub.loc[y0, "gas_fc_twh"]), float(sub.loc[y1, "gas_fc_twh"])
        d0, d1 = float(sub.loc[y0, "retailers_per_twh"]), float(sub.loc[y1, "retailers_per_twh"])

        d_ln_r = float(np.log(r1 / r0))
        d_ln_c = float(np.log(c1 / c0))
        denom_contrib = -d_ln_c
        d_ln_d = float(np.log(d1 / d0))
        # Exact identity check
        if abs((d_ln_r + denom_contrib) - d_ln_d) > 1e-10:
            raise AssertionError("Log-decomposition identity violated.")

        rows.append(
            {
                "geo": geo,
                "period": label,
                "y0": y0,
                "y1": y1,
                "retailers_y0": r0,
                "retailers_y1": r1,
                "retailers_pct_chg": 100.0 * (r1 - r0) / r0,
                "gas_twh_y0": c0,
                "gas_twh_y1": c1,
                "gas_twh_pct_chg": 100.0 * (c1 - c0) / c0,
                "density_y0": d0,
                "density_y1": d1,
                "density_pct_chg": 100.0 * (d1 - d0) / d0,
                "log_chg_total": d_ln_d,
                "log_chg_numerator_entry": d_ln_r,
                "log_chg_denominator_demand": denom_contrib,
                "share_from_numerator_pct": 100.0 * d_ln_r / d_ln_d if abs(d_ln_d) > 1e-9 else np.nan,
                "share_from_denominator_pct": 100.0 * denom_contrib / d_ln_d if abs(d_ln_d) > 1e-9 else np.nan,
            }
        )
    return pd.DataFrame(rows)


def fit_twoway_fe(frame: pd.DataFrame, outcome: str, predictor: str) -> dict[str, Any]:
    """Fit two-way fixed effects OLS (country + year FE) with country-clustered SEs and LOO check."""
    d = frame.dropna(subset=[outcome, predictor, "geo", "year"]).copy()
    counts = d.groupby("geo").size()
    valid_geos = counts[counts >= MIN_YEARS_FOR_FE].index
    d = d[d["geo"].isin(valid_geos)].sort_values(["geo", "year"]).copy()

    if d["geo"].nunique() < 5 or d["year"].nunique() < 3:
        raise RuntimeError(f"Insufficient panel groups for {outcome} ~ {predictor}")

    fe_only = smf.ols(f"{outcome} ~ C(geo) + C(year)", data=d).fit()
    full = smf.ols(f"{outcome} ~ {predictor} + C(geo) + C(year)", data=d).fit(
        cov_type="cluster",
        cov_kwds={"groups": d["geo"]},
    )

    coef = float(full.params[predictor])
    se = float(full.bse[predictor])
    pval = float(full.pvalues[predictor])
    ci_low, ci_high = (float(x) for x in full.conf_int().loc[predictor])
    within_r2 = float(1.0 - full.ssr / fe_only.ssr) if fe_only.ssr else np.nan

    # Leave-one-country-out stability test
    loo_rows = []
    for geo in sorted(d["geo"].unique()):
        held = d[d["geo"] != geo]
        try:
            sub_fit = smf.ols(f"{outcome} ~ {predictor} + C(geo) + C(year)", data=held).fit(
                cov_type="cluster", cov_kwds={"groups": held["geo"]}
            )
            sub_coef = float(sub_fit.params[predictor])
            loo_rows.append(
                {
                    "geo_dropped": geo,
                    "coef": sub_coef,
                    "same_sign": bool(np.sign(sub_coef) == np.sign(coef) and sub_coef != 0 and coef != 0),
                    "rel_abs_diff": abs(sub_coef - coef) / abs(coef) if coef != 0 else np.nan,
                }
            )
        except Exception:
            continue

    loo_df = pd.DataFrame(loo_rows)
    loo_same_sign = int(loo_df["same_sign"].sum()) if len(loo_df) else 0
    loo_within_band = int((loo_df["rel_abs_diff"] <= LOO_BAND).sum()) if len(loo_df) else 0
    passes_gate = bool(
        len(loo_df) > 0
        and loo_df["same_sign"].all()
        and (loo_df["rel_abs_diff"] <= LOO_BAND).all()
        and not (ci_low <= 0 <= ci_high)
    )

    return {
        "outcome": outcome,
        "predictor": predictor,
        "coef": coef,
        "se": se,
        "pval": pval,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "within_r2": within_r2,
        "n_obs": int(full.nobs),
        "n_countries": int(d["geo"].nunique()),
        "n_years": int(d["year"].nunique()),
        "loo_min": float(loo_df["coef"].min()) if len(loo_df) else np.nan,
        "loo_max": float(loo_df["coef"].max()) if len(loo_df) else np.nan,
        "loo_same_sign": loo_same_sign,
        "loo_within_band": loo_within_band,
        "loo_total": int(len(loo_df)),
        "passes_strict_gate": passes_gate,
        "loo_df": loo_df,
    }


def build_crisis_stress_test(panel: pd.DataFrame) -> pd.DataFrame:
    """Compare 2021 (pre-crisis) vs 2023 (peak shock) across all reporting EU-27 + Big-6 countries."""
    p21 = panel[panel["year"] == 2021].set_index("geo")
    p23 = panel[panel["year"] == 2023].set_index("geo")
    common = sorted(set(p21.index).intersection(p23.index))
    rows = []
    for geo in common:
        r21, r23 = p21.loc[geo], p23.loc[geo]
        rows.append(
            {
                "geo": geo,
                "country_name": r23["country_name"],
                "is_eu27": bool(r23["is_eu27"]),
                "is_big6": bool(r23["is_big6"]),
                "e_gen_share_2021": r21["e_gen_share"],
                "e_gen_share_2023": r23["e_gen_share"],
                "ren_elec_2021": r21["ren_elec_pct"],
                "ren_elec_2023": r23["ren_elec_pct"],
                "gas_retail_share_ge5_2023": r23["gas_retail_share_ge5"],
                "elec_eur_2021": r21["elec_price_eur_kwh"],
                "elec_eur_2023": r23["elec_price_eur_kwh"],
                "elec_eur_pct_chg": 100.0 * (r23["elec_price_eur_kwh"] - r21["elec_price_eur_kwh"]) / r21["elec_price_eur_kwh"]
                if pd.notna(r21["elec_price_eur_kwh"]) and r21["elec_price_eur_kwh"] > 0 and pd.notna(r23["elec_price_eur_kwh"])
                else np.nan,
                "elec_pps_2023": r23["elec_price_pps_kwh"],
                "elec_tax_share_2021": r21["elec_price_tax_share_pct"],
                "elec_tax_share_2023": r23["elec_price_tax_share_pct"],
                "gas_eur_2021": r21["gas_price_eur_kwh"],
                "gas_eur_2023": r23["gas_price_eur_kwh"],
                "gas_eur_pct_chg": 100.0 * (r23["gas_price_eur_kwh"] - r21["gas_price_eur_kwh"]) / r21["gas_price_eur_kwh"]
                if pd.notna(r21["gas_price_eur_kwh"]) and r21["gas_price_eur_kwh"] > 0 and pd.notna(r23["gas_price_eur_kwh"])
                else np.nan,
                "warm_total_2021": r21["unable_warm_total_pct"],
                "warm_total_2023": r23["unable_warm_total_pct"],
                "warm_total_pp_chg": r23["unable_warm_total_pct"] - r21["unable_warm_total_pct"],
                "warm_lowinc_2021": r21["unable_warm_lowinc_pct"],
                "warm_lowinc_2023": r23["unable_warm_lowinc_pct"],
                "warm_lowinc_pp_chg": r23["unable_warm_lowinc_pct"] - r21["unable_warm_lowinc_pct"],
                "warm_income_gap_2023": r23["unable_warm_income_gap_pp"],
                "arrears_total_2021": r21["utility_arrears_total_pct"],
                "arrears_total_2023": r23["utility_arrears_total_pct"],
                "arrears_lowinc_2023": r23["utility_arrears_lowinc_pct"],
            }
        )
    return pd.DataFrame(rows)


def share_direction(delta: float) -> str:
    """Classify 2013-2023 share shift against pre-registered +/-2 pp band."""
    if delta <= -SHARE_FLAT_PP:
        return "fell"
    if delta >= SHARE_FLAT_PP:
        return "rose"
    return "stayed within 2 percentage points"


def density_direction(old: float, new: float) -> str:
    """Classify density shift against pre-registered +/-10% band."""
    if old == 0:
        return "rose" if new > 0 else "stayed within 10 percent"
    rel = (new - old) / abs(old)
    if rel <= -DENSITY_FLAT_REL:
        return "fell"
    if rel >= DENSITY_FLAT_REL:
        return "rose"
    return "stayed within 10 percent"


def run_all_analytics(panel: pd.DataFrame) -> dict[str, Any]:
    """Execute all four analytical pillars and return structured results dictionary."""
    eu27_panel = panel[panel["is_eu27"]].copy()
    big6_panel = panel[panel["is_big6"]].copy()

    # Pillar 1: Electricity concentration & renewable transition across 3 comparator cohorts
    p1_all = {col: yearly_distribution(panel, col) for col in ("e_cap_share", "e_gen_share", "e_cap_top", "e_gen_top", "ren_elec_pct")}
    p1_bal_eu27 = {
        col: yearly_distribution(balanced_cohort(panel, col, eu27_only=True), col)
        for col in ("e_cap_share", "e_gen_share", "e_cap_top", "e_gen_top", "ren_elec_pct")
    }
    p1_big6 = {col: yearly_distribution(big6_panel, col) for col in ("e_cap_share", "e_gen_share", "e_cap_top", "e_gen_top", "ren_elec_pct")}

    # Pillar 2: Gas retail density, denominator log-decomposition, and true retail concentration (GRTL_NG5)
    density_base = panel[panel["in_density_sample"]].copy()
    p2_density_all = yearly_distribution(density_base, "retailers_per_twh")
    p2_density_eu27 = yearly_distribution(density_base[density_base["is_eu27"]], "retailers_per_twh")
    p2_density_big6 = yearly_distribution(density_base[density_base["is_big6"]], "retailers_per_twh")
    p2_per_million = yearly_distribution(density_base.dropna(subset=["retailers_per_million"]), "retailers_per_million")
    p2_gas_conc_all = yearly_distribution(panel, "gas_retail_share_ge5")
    p2_gas_conc_big6 = yearly_distribution(big6_panel, "gas_retail_share_ge5")
    p2_decomp_de = decompose_retailer_density(panel, "DE")

    excluded_density = panel[
        panel["gas_retailers"].notna() & (panel["gas_fc_gwh"].isna() | (panel["gas_fc_gwh"] < GAS_FLOOR_GWH))
    ][["geo", "year", "gas_retailers", "gas_fc_gwh"]].copy()
    excluded_density["reason"] = np.where(excluded_density["gas_fc_gwh"].isna(), "missing_final_consumption", "below_1_twh")

    # Pillar 3: Household affordability & tax-wedge dynamics
    p3_elec_eur_eu27 = yearly_distribution(eu27_panel, "elec_price_eur_kwh")
    p3_elec_pps_eu27 = yearly_distribution(eu27_panel, "elec_price_pps_kwh")
    p3_elec_tax_eu27 = yearly_distribution(eu27_panel, "elec_price_tax_share_pct")
    p3_gas_eur_eu27 = yearly_distribution(eu27_panel, "gas_price_eur_kwh")
    p3_gas_pps_eu27 = yearly_distribution(eu27_panel, "gas_price_pps_kwh")

    # Pillar 4: Social cohesion (energy poverty & utility arrears)
    p4_warm_total_eu27 = yearly_distribution(eu27_panel, "unable_warm_total_pct")
    p4_warm_lowinc_eu27 = yearly_distribution(eu27_panel, "unable_warm_lowinc_pct")
    p4_arrears_total_eu27 = yearly_distribution(eu27_panel, "utility_arrears_total_pct")
    p4_arrears_lowinc_eu27 = yearly_distribution(eu27_panel, "utility_arrears_lowinc_pct")
    crisis_table = build_crisis_stress_test(panel)

    # Panel TWFE Models (all evaluated against strict LOO + 95% CI gate)
    # Note: EU-27 sample used for policy/social regressions to avoid mixing non-EU survey regimes
    models_spec = [
        ("m1_ren_to_deconc_all", panel, "e_gen_share", "ren_elec_pct", "Electricity generation concentration on renewable elec. share (All)"),
        ("m2_ren_to_deconc_eu27", eu27_panel, "e_gen_share", "ren_elec_pct", "Electricity generation concentration on renewable elec. share (EU-27)"),
        ("m3_conc_to_elec_pps", eu27_panel, "elec_price_pps_kwh", "e_gen_share", "Household electricity price (PPS/kWh) on generation concentration (EU-27)"),
        ("m4_elec_pps_to_warm_all", eu27_panel, "unable_warm_total_pct", "elec_price_pps_kwh", "Inability to keep warm (Total %) on electricity price PPS (EU-27)"),
        ("m5_gas_pps_to_warm_lowinc", eu27_panel, "unable_warm_lowinc_pct", "gas_price_pps_kwh", "Low-income inability to keep warm (%) on gas price PPS (EU-27)"),
        ("m6_conc_to_warm_total", eu27_panel, "unable_warm_total_pct", "e_gen_share", "Inability to keep warm (Total %) on generation concentration (EU-27)"),
        ("m7_legacy_rq3_density", density_base, "retailers_per_twh", "e_gen_share", "Legacy v2 audit check: Gas retailer density on elec. gen. concentration"),
    ]
    model_results: dict[str, dict[str, Any]] = {}
    model_summary_rows = []
    for key, df_m, y_col, x_col, desc in models_spec:
        res = fit_twoway_fe(df_m, y_col, x_col)
        res["description"] = desc
        model_results[key] = res
        model_summary_rows.append(
            {
                "model_id": key,
                "description": desc,
                "outcome": y_col,
                "predictor": x_col,
                "coef": res["coef"],
                "se": res["se"],
                "pval": res["pval"],
                "ci_low": res["ci_low"],
                "ci_high": res["ci_high"],
                "within_r2": res["within_r2"],
                "n_obs": res["n_obs"],
                "n_countries": res["n_countries"],
                "loo_min": res["loo_min"],
                "loo_max": res["loo_max"],
                "loo_same_sign": f"{res['loo_same_sign']}/{res['loo_total']}",
                "loo_within_50pct": f"{res['loo_within_band']}/{res['loo_total']}",
                "passes_strict_gate": res["passes_strict_gate"],
            }
        )
    models_df = pd.DataFrame(model_summary_rows)

    return {
        "p1_all": p1_all,
        "p1_bal_eu27": p1_bal_eu27,
        "p1_big6": p1_big6,
        "p2_density_all": p2_density_all,
        "p2_density_eu27": p2_density_eu27,
        "p2_density_big6": p2_density_big6,
        "p2_per_million": p2_per_million,
        "p2_gas_conc_all": p2_gas_conc_all,
        "p2_gas_conc_big6": p2_gas_conc_big6,
        "p2_decomp_de": p2_decomp_de,
        "excluded_density": excluded_density,
        "p3_elec_eur_eu27": p3_elec_eur_eu27,
        "p3_elec_pps_eu27": p3_elec_pps_eu27,
        "p3_elec_tax_eu27": p3_elec_tax_eu27,
        "p3_gas_eur_eu27": p3_gas_eur_eu27,
        "p3_gas_pps_eu27": p3_gas_pps_eu27,
        "p4_warm_total_eu27": p4_warm_total_eu27,
        "p4_warm_lowinc_eu27": p4_warm_lowinc_eu27,
        "p4_arrears_total_eu27": p4_arrears_total_eu27,
        "p4_arrears_lowinc_eu27": p4_arrears_lowinc_eu27,
        "crisis_table": crisis_table,
        "model_results": model_results,
        "models_df": models_df,
    }
