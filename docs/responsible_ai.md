# Responsible AI Disclosure

This project uses AI as an engineering and documentation accelerator under strict human analytical governance.

## How AI Assistance Was Used
- **Upstream ETL & packaging:** Assisting with Python Eurostat API ingestion, Matplotlib figure styling, repository structuring, and documentation drafting.
- **Debugging & refactoring:** Cleaning personal local paths, modularizing SQL scripts into portable numbered files, and identifying lint/schema alignment issues.

## What Was Independently Owned & Validated
- **Problem framing & methodological restraint:** Defining the five policy-relevant analytical questions, choosing peer cohorts transparently, enforcing non-causal language, and rejecting unsupported v1 variable labels (documented in [`METHODOLOGICAL_AUDIT_LOG.md`](../METHODOLOGICAL_AUDIT_LOG.md)).
- **Hands-on analytical execution:** Running R grain/datatype profiling, diagnosing and rejecting the flawed direct MySQL CSV import, executing the controlled `TEXT` staging → typed `master_panel` transformation (`396` rows, `0` warnings), running all five MySQL queries and five `vw_tableau_*` views, and building the single Tableau executive dashboard.
- **Independent quantitative verification:** Every headline number in `README.md`, `docs/`, and the Tableau dashboard was cross-checked directly against actual MySQL query outputs and automated Python unit-test recalculations (`tests/test_pipeline.py`).
- **Claim review:** All AI-assisted prose was audited to remove causal overclaims, unverified source attributions, and unsupported decomposition of ex-tax electricity prices.
