# Methodological Audit Log & AI-Era Analytical Governance

This document records the full evolution of this repository from an early, error-prone draft (**v1**) through a disciplined descriptive reset (**v2**) to the current production-grade, multi-source analytics suite (**v3 — Track A**). In the era of AI-assisted analysis, **transparent error detection, provenance auditing, and human domain skepticism** are core senior-analyst competencies.

---

## Evolution Summary

| Version | Scope | Core Strength | Critical Flaw Identified & Remediated |
|---|---|---|---|
| **v1 (Sept 2025)** | Single Eurostat TSV (`nrg_ind_market`) stretched into a "Social Cohesion & Price Competitiveness" report | Ambitious framing | **Catastrophic variable mislabeling:** `CMPY_ECAP5` & `CMPY_EG5` (electricity market concentration shares) were mislabeled as "electricity/gas price competitiveness", `GRTL` (gas retailer count) as "grid infrastructure", and `LCMPY_IECAP` as "low-carbon electricity". No real price or social cohesion data existed. |
| **v2 (Sept 2026)** | Rebuilt reproducible script (`run_pipeline.py`) + LaTeX note (`main.tex`) + `CODEBOOK.md` | Caught v1 mislabeling; added Germany-2013 unit checks, pre-registered thresholds, and a strict leave-one-out (LOO) gate | **Analytical & engineering debt:** (1) Left 20+ withdrawn files, stale v1 LaTeX tables, and broken Conda CI in the repo; (2) Missed that Germany's 2021–2023 gas-retailer density spike (`+25.7%`) was a **102.7% denominator illusion** caused by a `-20.9%` crisis drop in gas consumption; (3) Benchmarked against an unbalanced 35-country sample skewed by micro-markets; (4) Kept an orphaned RQ3 regression across unrelated markets while abandoning the title's social-cohesion question. |
| **v3 / Track A (Nov 2026)** | Modular Python package (`src/energiewende`), 8 official Eurostat datasets, automated tests, CI, auto-populated LaTeX, and GitHub Pages Executive Dashboard | **Full end-to-end decision intelligence** backed by real renewables, household price/tax-wedge, and EU-SILC energy poverty data | Directly answers the Energiewende market-structure-to-social-resilience question with zero hardcoded number drift, cryptographic SHA-256 provenance (`data/manifest.json`), and explicit causal guardrails. |

---

## Key Senior-Analyst Audit Catches Enforced in Code

1. **Automated Unit-Check Contracts (`src/energiewende/ingestion.py`):**
   - Pipeline fails fast if Germany 2013 benchmark values drift (`CMPY_ECAP5 = 67.0%`, `CMPY_EG5 = 74.0%`, `LCMPY_IECAP = 29.0%`, `GRTL = 825`, `GRTL_NG5 = 26.0%`, `pop = 80,523,746`).
   - Enforces that `GE` (Georgia) is never collapsed into `DE` (Germany) and distinguishes strictly bounded `[0, 100.5]` shares from Eurostat RED II `ren_elec_pct` (which legitimately exceeds `100%` in net-exporting hydro economies like Norway).

2. **Ratio Denominator Audit (`src/energiewende/analytics.py`):**
   - Enforces the exact identity $\Delta \ln(R / C) \equiv \Delta \ln(R) - \Delta \ln(C)$ in unit tests (`test_exact_log_decomposition_identity`), exposing that Germany's 2021–2023 `retailers/TWh` increase occurred while retailer counts actually fell.

3. **Benchmark Cohort Sensitivity Control:**
   - Every electricity concentration comparison reports **All Reporters (unbalanced)**, **Balanced EU-27 (constant N=26)**, and **Big-6 Large Markets (`DE, FR, IT, ES, PL, NL`)** side by side so micro-market sample entry cannot distort conclusions.

4. **Anti-P-Hacking Econometric Gate:**
   - All 7 Two-Way Fixed Effects regressions (country + year FE, country-clustered SEs) face the same pre-registered gate: **100% leave-one-country-out sign preservation, ≤50% coefficient drift, and 95% CI excluding zero**. Models M1–M3 pass; Models M4–M7 fail and are transparently reported as failing rather than hidden.

5. **Single Source of Truth (SSOT) Reporting:**
   - `paper/generated_macros.tex`, `paper/tables/*.tex`, `outputs/RESULTS.md`, and `docs/index.html` are all generated programmatically from the same validated DataFrame, eliminating manual transcription drift.
