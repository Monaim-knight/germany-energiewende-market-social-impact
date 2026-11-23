"""End-to-end reproducible CLI pipeline for the Track A Energiewende Analytics Suite."""

from __future__ import annotations

import argparse

from energiewende.analytics import run_all_analytics
from energiewende.config import DOCS, FIGURES, OUTPUTS, TABLES
from energiewende.dashboard import build_dashboard
from energiewende.ingestion import build_master_panel
from energiewende.reporting import (
    export_csv_tables,
    write_latex_macros_and_tables,
    write_results_markdown,
)
from energiewende.visuals import generate_all_figures


def run_pipeline(refresh: bool = False) -> None:
    """Execute ingestion, validation, analytics, visuals, LaTeX macros, and dashboard build."""
    panel, manifest = build_master_panel(refresh=refresh)
    results = run_all_analytics(panel)

    export_csv_tables(results, TABLES)
    write_latex_macros_and_tables(panel, results)
    write_results_markdown(panel, results, OUTPUTS / "RESULTS.md")
    figs = generate_all_figures(panel, results, FIGURES)
    dash = build_dashboard(panel, results, manifest, DOCS / "index.html")

    passing = results["models_df"][results["models_df"]["passes_strict_gate"]]["model_id"].tolist()
    print(f"Master panel: {len(panel)} rows x {panel.shape[1]} cols ({panel['geo'].nunique()} countries)")
    print(f"Generated {len(figs)} publication figures in {FIGURES}")
    print(f"Models passing strict 100% LOO + 95% CI gate: {passing}")
    print(f"Wrote interactive executive dashboard: {dash}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Track A Energiewende Analytics Pipeline.")
    parser.add_argument("--refresh", action="store_true", help="Re-download Eurostat API tables instead of using local cache.")
    args = parser.parse_args()
    run_pipeline(refresh=args.refresh)


if __name__ == "__main__":
    main()
