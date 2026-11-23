"""Publication-grade Matplotlib figures (300 DPI PNG + vector SVG) for all four pillars."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Clean editorial color palette (colorblind-safe, print-ready)
NAVY = "#0B3A66"
TEAL = "#1F7A8C"
AMBER = "#D97706"
CRIMSON = "#B91C1C"
SLATE = "#475569"
LIGHT_GRAY = "#E2E8F0"
MID_GRAY = "#94A3B8"
GREEN = "#15803D"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "axes.edgecolor": "#CBD5E1",
        "axes.linewidth": 0.9,
        "axes.titlesize": 11.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.8,
        "xtick.labelsize": 8.8,
        "ytick.labelsize": 8.8,
        "legend.fontsize": 8.6,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    }
)


def _clean_ax(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.5, color="#CBD5E1")
    ax.set_axisbelow(True)


def _save(fig: plt.Figure, base_path: Path) -> None:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(base_path.with_suffix(".png"), dpi=300, bbox_inches="tight")
    fig.savefig(base_path.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)


def plot_fig1_electricity_transition(panel: pd.DataFrame, res: dict[str, Any], out_dir: Path) -> None:
    """Two-panel figure: cohort sensitivity in concentration + Germany renewable/capacity surge."""
    bal = res["p1_bal_eu27"]["e_gen_share"]
    big6 = res["p1_big6"]["e_gen_share"]
    de = panel[panel["geo"] == "DE"].sort_values("year")
    years = bal["year"].to_numpy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 4.9))

    # Panel A: Concentration vs Balanced EU-27 IQR & Big-6 Median
    ax1.fill_between(years, bal["p25"], bal["p75"], color=LIGHT_GRAY, alpha=0.85, label="Balanced EU-27 IQR (N=26)")
    ax1.plot(years, bal["median"], color=SLATE, linewidth=1.7, linestyle="--", label="Balanced EU-27 median")
    ax1.plot(years, big6["median"], color=AMBER, linewidth=2.0, linestyle="-.", label="Big-6 peer median")
    ax1.plot(years, bal["de"], color=NAVY, linewidth=2.6, marker="o", markersize=4.2, label="Germany")
    ax1.annotate("DE: 74.0%", (2013, 74.0), xytext=(2013.2, 81.5), fontsize=8.5, fontweight="bold", color=NAVY)
    ax1.annotate("DE: 57.1%\n(#2 of 6 Big-6)", (2023, 57.1), xytext=(2019.6, 67.5), fontsize=8.3, fontweight="bold", color=NAVY,
                 arrowprops={"arrowstyle": "->", "color": NAVY, "lw": 0.9})
    ax1.annotate("Big-6 med:\n42.1%", (2023, 42.15), xytext=(2020.2, 34.0), fontsize=8.1, color=AMBER,
                 arrowprops={"arrowstyle": "->", "color": AMBER, "lw": 0.9})
    ax1.set_title("A. Electricity Generation Concentration: Peer-Cohort Effect")
    ax1.set_ylabel("Cumulative share of firms ≥5% (%)")
    ax1.set_xlabel("Year")
    ax1.set_xticks(years[::2])
    ax1.set_ylim(28, 95)
    _clean_ax(ax1)
    ax1.legend(frameon=False, loc="lower left", ncol=1)

    # Panel B: Germany Renewable Electricity Share + Connected/Decommissioned Capacity (GW)
    x = de["year"].to_numpy()
    w = 0.36
    ax2.bar(x - w / 2, de["e_cap_connected_mw"] / 1000.0, width=w, color=TEAL, alpha=0.85, label="New capacity connected (GW)")
    ax2.bar(x + w / 2, de["e_cap_decomm_mw"] / 1000.0, width=w, color=CRIMSON, alpha=0.75, label="Capacity decommissioned (GW)")
    ax2.set_ylabel("Annual capacity flow (GW)", color=SLATE)
    ax2.set_xlabel("Year")
    ax2.set_xticks(x[::2])
    ax2.set_ylim(0, 27)
    _clean_ax(ax2)

    ax2b = ax2.twinx()
    ax2b.plot(x, de["ren_elec_pct"], color=NAVY, linewidth=2.5, marker="s", markersize=4.5, label="Renewable electricity share (%)")
    ax2b.set_ylabel("Renewable electricity share (%)", color=NAVY)
    ax2b.set_ylim(15, 62)
    ax2b.spines["top"].set_visible(False)
    ax2b.tick_params(axis="y", colors=NAVY)
    ax2b.annotate("51.9%", (2023, 51.95), xytext=(2021.3, 56.5), fontsize=8.8, fontweight="bold", color=NAVY,
                  arrowprops={"arrowstyle": "->", "color": NAVY, "lw": 0.9})
    ax2.set_title("B. Germany: Renewable Surge & Grid Capacity Turnover")

    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2b.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, frameon=False, loc="upper left")

    fig.suptitle("Pillar 1: Energiewende Deconcentration Depends on Your Benchmark Cohort", fontsize=13, fontweight="bold", y=1.02)
    fig.text(0.5, -0.04, "Sources: Eurostat nrg_ind_market & nrg_ind_ren (2013–2023). Big-6 peers: DE, FR, IT, ES, PL, NL.",
             ha="center", fontsize=8.3, color=SLATE)
    fig.tight_layout()
    _save(fig, out_dir / "fig1_electricity_transition_cohorts")


def plot_fig2_gas_decomposition(panel: pd.DataFrame, res: dict[str, Any], out_dir: Path) -> None:
    """Two-panel figure exposing the 2021-2023 gas demand collapse illusion in retailer density."""
    de = panel[panel["geo"] == "DE"].sort_values("year")
    decomp = res["p2_decomp_de"]

    years = de["year"].to_numpy()
    idx_ret = 100.0 * de["gas_retailers"] / float(de.iloc[0]["gas_retailers"])
    idx_gas = 100.0 * de["gas_fc_twh"] / float(de.iloc[0]["gas_fc_twh"])
    idx_den = 100.0 * de["retailers_per_twh"] / float(de.iloc[0]["retailers_per_twh"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 4.9))

    # Panel A: Indexed trajectories (2013 = 100)
    ax1.axvspan(2021, 2023, color="#FEE2E2", alpha=0.55, label="2021–2023 gas crisis shock")
    ax1.axhline(100, color=MID_GRAY, linewidth=0.9, linestyle=":")
    ax1.plot(years, idx_den, color=NAVY, linewidth=2.6, marker="o", markersize=4.3, label="Retailers / TWh (ratio)")
    ax1.plot(years, idx_ret, color=TEAL, linewidth=2.0, linestyle="--", label="Retailer count (numerator)")
    ax1.plot(years, idx_gas, color=CRIMSON, linewidth=2.2, linestyle="-.", label="Final gas consumption (denominator)")
    ax1.annotate("Ratio jumps +25.7%\nwhile retailers fall -0.6%", (2022.4, 132), xytext=(2016.2, 131),
                 fontsize=8.3, fontweight="bold", color=NAVY,
                 arrowprops={"arrowstyle": "->", "color": NAVY, "lw": 0.9})
    ax1.annotate("Gas use -20.9%\n(698 → 552 TWh)", (2023, float(idx_gas.iloc[-1])), xytext=(2017.8, 80),
                 fontsize=8.2, fontweight="bold", color=CRIMSON,
                 arrowprops={"arrowstyle": "->", "color": CRIMSON, "lw": 0.9})
    ax1.set_title("A. Germany: Numerator vs. Denominator Divergence (2013 = 100)")
    ax1.set_ylabel("Index (2013 = 100)")
    ax1.set_xlabel("Year")
    ax1.set_xticks(years[::2])
    ax1.set_ylim(75, 148)
    _clean_ax(ax1)
    ax1.legend(frameon=False, loc="lower left")

    # Panel B: Log-decomposition bar chart across regimes
    labels = ["Full Decade\n(2013–2023)", "Entry Phase\n(2013–2017)", "Plateau\n(2017–2021)", "Crisis Shock\n(2021–2023)"]
    num = decomp["log_chg_numerator_entry"].to_numpy() * 100.0
    den = decomp["log_chg_denominator_demand"].to_numpy() * 100.0
    tot = decomp["log_chg_total"].to_numpy() * 100.0

    xpos = np.arange(len(labels))
    w = 0.28
    ax2.axhline(0, color=SLATE, linewidth=0.9)
    ax2.bar(xpos - w, num, width=w, color=TEAL, label="Retailer entry (+Δ ln Retailers)")
    ax2.bar(xpos, den, width=w, color=CRIMSON, label="Demand contraction (-Δ ln TWh)")
    ax2.bar(xpos + w, tot, width=w, color=NAVY, label="Net density change (Δ ln Ratio)")

    for i in range(len(labels)):
        ax2.text(xpos[i] + w, tot[i] + (1.2 if tot[i] >= 0 else -2.8), f"{tot[i]:+.1f}", ha="center", fontsize=8.2, fontweight="bold", color=NAVY)
        if i == 3:
            ax2.text(xpos[i], den[i] + 1.2, f"{den[i]:+.1f}", ha="center", fontsize=8.2, fontweight="bold", color=CRIMSON)

    ax2.set_title("B. Exact Log-Decomposition of Density Growth (×100 log pts)")
    ax2.set_ylabel("Log-point contribution (×100)")
    ax2.set_xticks(xpos)
    ax2.set_xticklabels(labels)
    ax2.set_ylim(-15, 38)
    _clean_ax(ax2)
    ax2.legend(frameon=False, loc="upper right")

    fig.suptitle("Pillar 2: The Gas-Retailer Density Spike Was a 2022–2023 Demand-Collapse Artifact", fontsize=13, fontweight="bold", y=1.02)
    fig.text(0.5, -0.04, "Sources: Eurostat nrg_ind_market (GRTL) & nrg_bal_s (FC_E + FC_NE). Exact identity: Δ ln(R/C) = Δ ln(R) - Δ ln(C).",
             ha="center", fontsize=8.3, color=SLATE)
    fig.tight_layout()
    _save(fig, out_dir / "fig2_gas_density_decomposition")


def plot_fig3_affordability_tax_wedge(panel: pd.DataFrame, out_dir: Path) -> None:
    """Two-panel figure: Germany electricity price tax-wedge regime shift + Big-6 2023 comparison."""
    de = panel[panel["geo"] == "DE"].sort_values("year")
    b6_23 = panel[(panel["is_big6"]) & (panel["year"] == 2023)].sort_values("elec_price_eur_kwh", ascending=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 4.9))

    # Panel A: Stacked bar of Germany electricity price (Ex-Tax vs Taxes/Levies)
    years = de["year"].to_numpy()
    extax = de["elec_price_extax_eur_kwh"].to_numpy()
    tax_wedge = (de["elec_price_eur_kwh"] - de["elec_price_extax_eur_kwh"]).to_numpy()
    tax_pct = de["elec_price_tax_share_pct"].to_numpy()

    ax1.bar(years, extax, width=0.65, color=NAVY, label="Energy & network (ex-tax, EUR/kWh)")
    ax1.bar(years, tax_wedge, bottom=extax, width=0.65, color=AMBER, alpha=0.85, label="Taxes & levies incl. EEG (EUR/kWh)")
    for y, tot, tp in zip(years, de["elec_price_eur_kwh"], tax_pct):
        if y in (2013, 2017, 2021, 2023):
            ax1.text(y, tot + 0.010, f"€{tot:.2f}\n({tp:.0f}% tax)", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color=SLATE)
    ax1.annotate("EEG levy abolished\n(tax share 51% → 28%)\nbut ex-tax +85%", (2022, 0.335), xytext=(2014.2, 0.395),
                 fontsize=8.2, fontweight="bold", color=CRIMSON,
                 arrowprops={"arrowstyle": "->", "color": CRIMSON, "lw": 1.0, "connectionstyle": "arc3,rad=-0.12"})
    ax1.set_title("A. Germany Household Electricity Price & Tax-Wedge Shift")
    ax1.set_ylabel("EUR per kWh (Band DC: 2,500–4,999 kWh)")
    ax1.set_xlabel("Year")
    ax1.set_xticks(years[::2])
    ax1.set_ylim(0, 0.50)
    _clean_ax(ax1)
    ax1.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2)

    # Panel B: Big-6 2023 Electricity Prices (EUR vs PPS)
    y_pos = np.arange(len(b6_23))
    h = 0.36
    colors_eur = [NAVY if g == "DE" else TEAL for g in b6_23["geo"]]
    ax2.barh(y_pos + h / 2, b6_23["elec_price_eur_kwh"], height=h, color=colors_eur, label="Nominal EUR / kWh")
    ax2.barh(y_pos - h / 2, b6_23["elec_price_pps_kwh"], height=h, color=MID_GRAY, alpha=0.85, label="Purchasing Power Standard (PPS / kWh)")
    for i, row in enumerate(b6_23.itertuples(index=False)):
        ax2.text(row.elec_price_eur_kwh + 0.006, i + h / 2, f"€{row.elec_price_eur_kwh:.3f}", va="center", fontsize=8.0, fontweight="bold" if row.geo == "DE" else "normal")
        ax2.text(row.elec_price_pps_kwh + 0.006, i - h / 2, f"{row.elec_price_pps_kwh:.3f}", va="center", fontsize=7.8, color=SLATE)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(b6_23["country_name"])
    ax2.set_xlim(0, 0.49)
    ax2.set_xlabel("Price per kWh (all taxes included, 2023 annual mean)")
    ax2.set_title("B. Big-6 Affordability Comparison: Nominal vs. PPS (2023)")
    _clean_ax(ax2)
    ax2.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2)

    fig.suptitle("Pillar 3: Abolishing the EEG Levy Softened—But Did Not Reverse—Germany's Price Surge", fontsize=13, fontweight="bold", y=1.02)
    fig.text(0.5, -0.09, "Source: Eurostat nrg_pc_204 (Band DC, S1/S2 annual average, I_TAX & X_TAX, EUR & PPS).",
             ha="center", fontsize=8.3, color=SLATE)
    fig.tight_layout()
    _save(fig, out_dir / "fig3_affordability_tax_wedge")


def plot_fig4_social_cohesion(panel: pd.DataFrame, res: dict[str, Any], out_dir: Path) -> None:
    """Two-panel social cohesion figure: Germany vs EU-27 energy poverty + Big-6 low-income shock."""
    wt = res["p4_warm_total_eu27"]
    wl = res["p4_warm_lowinc_eu27"]
    crisis = res["crisis_table"]
    b6 = crisis[crisis["is_big6"]].sort_values("warm_lowinc_2023", ascending=True)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.1))

    # Panel A: Germany vs EU-27 Median (Total and Low-Income <60% median)
    years = wt["year"].to_numpy()
    ax1.plot(years, wl["de"], color=CRIMSON, linewidth=2.5, marker="s", markersize=4.3, label="Germany: Low-income (<60% median)")
    ax1.plot(years, wl["median"], color=CRIMSON, linewidth=1.5, linestyle="--", alpha=0.65, label="EU-27 median: Low-income")
    ax1.plot(years, wt["de"], color=NAVY, linewidth=2.5, marker="o", markersize=4.3, label="Germany: Total population")
    ax1.plot(years, wt["median"], color=SLATE, linewidth=1.5, linestyle="--", alpha=0.75, label="EU-27 median: Total population")
    ax1.axvline(2020, color=MID_GRAY, linewidth=1.0, linestyle=":")
    ax1.text(2019.85, 19.6, "2020 DE\nsurvey break", ha="right", va="top", fontsize=7.8, color=SLATE)
    ax1.annotate("DE Total crosses above EU-27 med\n(8.2% vs 7.1% in 2023)", (2023, 8.2), xytext=(2014.4, 0.8),
                 fontsize=8.0, fontweight="bold", color=NAVY,
                 arrowprops={"arrowstyle": "->", "color": NAVY, "lw": 1.0, "connectionstyle": "arc3,rad=0.14"})
    ax1.set_title("A. Inability to Keep Home Warm: Germany vs. EU-27")
    ax1.set_ylabel("Share of population (%)")
    ax1.set_xlabel("Year")
    ax1.set_xticks(years[::2])
    ax1.set_ylim(0, 22)
    _clean_ax(ax1)
    ax1.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2, fontsize=8.0)

    # Panel B: Big-6 Dumbbell Chart (2021 vs 2023 Low-Income Energy Poverty)
    y_pos = np.arange(len(b6))
    for i, row in enumerate(b6.itertuples(index=False)):
        col = NAVY if row.geo == "DE" else SLATE
        lw = 3.0 if row.geo == "DE" else 2.0
        ax2.plot([row.warm_lowinc_2021, row.warm_lowinc_2023], [i, i], color=col, linewidth=lw, alpha=0.8)
        ax2.scatter([row.warm_lowinc_2021], [i], color=TEAL, s=55, zorder=4, label="2021 (pre-crisis)" if i == 0 else "")
        ax2.scatter([row.warm_lowinc_2023], [i], color=CRIMSON, s=65, zorder=5, label="2023 (post-shock)" if i == 0 else "")
        ax2.text(row.warm_lowinc_2023 + 0.8, i, f"{row.warm_lowinc_2023:.1f}% ({row.warm_lowinc_pp_chg:+.1f} pp)",
                 va="center", fontsize=8.2, fontweight="bold" if row.geo == "DE" else "normal", color=NAVY if row.geo == "DE" else SLATE)
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(b6["country_name"])
    ax2.set_xlim(0, 45)
    ax2.set_xlabel("Low-income (<60% median) inability to keep home warm (%)")
    ax2.set_title("B. Big-6 Low-Income Energy Poverty Shock (2021 → 2023)")
    _clean_ax(ax2)
    ax2.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2)

    fig.suptitle("Pillar 4: Social Cohesion Stress Test — Sharp German Deterioration, Lower Absolute Level Than Peers", fontsize=12.6, fontweight="bold", y=1.02)
    fig.text(0.5, -0.09, "Source: Eurostat EU-SILC ilc_mdes01 (TOTAL & B_60 income groups, 2013–2023). Note: Germany had an EU-SILC sampling/methodology break in 2020.",
             ha="center", fontsize=8.2, color=SLATE)
    fig.tight_layout()
    _save(fig, out_dir / "fig4_social_cohesion_stress_test")


def plot_fig5_twfe_stability(res: dict[str, Any], out_dir: Path) -> None:
    """Horizontal standardized t-stat / LOO stability chart for all 7 pre-registered TWFE checks."""
    df = res["models_df"].copy()
    # Compute t-stat and 95% CI in standardized z-units so models on different units can be compared cleanly
    df["t_stat"] = df["coef"] / df["se"]
    df["t_low"] = df["ci_low"] / df["se"]
    df["t_high"] = df["ci_high"] / df["se"]

    short_labels = {
        "m1_ren_to_deconc_all": "M1: Elec. concentration ~ Renewable share (All, N=359)",
        "m2_ren_to_deconc_eu27": "M2: Elec. concentration ~ Renewable share (EU-27, N=291)",
        "m3_conc_to_elec_pps": "M3: Elec. price (PPS) ~ Elec. concentration (EU-27, N=291)",
        "m4_elec_pps_to_warm_all": "M4: Energy poverty (Total) ~ Elec. price PPS (EU-27, N=297)",
        "m5_gas_pps_to_warm_lowinc": "M5: Low-income poverty ~ Gas price PPS (EU-27, N=264)",
        "m6_conc_to_warm_total": "M6: Energy poverty (Total) ~ Elec. concentration (EU-27, N=291)",
        "m7_legacy_rq3_density": "M7 (Legacy v2): Gas density ~ Elec. concentration (N=326)",
    }
    df["label"] = df["model_id"].map(short_labels)
    df = df.iloc[::-1].reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(11.4, 4.9))
    ax.axvline(0, color=SLATE, linewidth=1.0)
    ax.axvspan(-1.96, 1.96, color=LIGHT_GRAY, alpha=0.6, label="|t| < 1.96 (95% CI includes zero)")

    y_pos = np.arange(len(df))
    for i, row in enumerate(df.itertuples(index=False)):
        col = GREEN if row.passes_strict_gate else MID_GRAY
        ax.plot([row.t_low, row.t_high], [i, i], color=col, linewidth=2.6)
        ax.scatter([row.t_stat], [i], color=col, s=65, zorder=5)
        tag = f"PASS (LOO {row.loo_within_50pct}, R²w={row.within_r2:.3f})" if row.passes_strict_gate else f"FAIL GATE (LOO {row.loo_within_50pct}, R²w={row.within_r2:.3f})"
        ax.text(4.8, i, tag, va="center", fontsize=8.0, fontweight="bold" if row.passes_strict_gate else "normal",
                color=GREEN if row.passes_strict_gate else SLATE)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(df["label"])
    ax.set_xlim(-5.2, 9.8)
    ax.set_xlabel("Cluster-robust t-statistic with 95% confidence interval (country + year fixed effects)")
    ax.set_title("Panel Econometrics Audit: Strict Leave-One-Out & 95% CI Stability Gate")
    _clean_ax(ax)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.17))
    fig.text(0.5, -0.09, "All models include country & year fixed effects with country-clustered SEs. Strict gate requires 100% LOO sign preservation, <=50% coefficient drift, and 95% CI excluding zero.",
             ha="center", fontsize=8.1, color=SLATE)
    fig.tight_layout()
    _save(fig, out_dir / "fig5_twfe_stability_gate")


def generate_all_figures(panel: pd.DataFrame, res: dict[str, Any], out_dir: Path) -> list[Path]:
    """Generate all five Track A figures and return their PNG paths."""
    plot_fig1_electricity_transition(panel, res, out_dir)
    plot_fig2_gas_decomposition(panel, res, out_dir)
    plot_fig3_affordability_tax_wedge(panel, out_dir)
    plot_fig4_social_cohesion(panel, res, out_dir)
    plot_fig5_twfe_stability(res, out_dir)
    return sorted(out_dir.glob("*.png"))
