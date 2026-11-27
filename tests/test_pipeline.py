"""Automated data contracts, mathematical identities, and analytical integrity tests.

Compatible with both stdlib `python -m unittest` and `pytest`.
"""

from __future__ import annotations

import json
import re
import unittest

from energiewende.analytics import (
    balanced_cohort,
    decompose_retailer_density,
    run_all_analytics,
)
from energiewende.config import (
    DOCS,
    FIGURES,
    MANIFEST_PATH,
    OUTPUTS,
    PAPER,
    PAPER_TABLES,
    ROOT,
    YEAR_MAX,
    YEAR_MIN,
)
from energiewende.eurostat import sha256_file
from energiewende.ingestion import build_master_panel


class TestTrackAPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.panel, cls.manifest = build_master_panel(refresh=False)
        cls.res = run_all_analytics(cls.panel)

    def test_primary_key_and_window(self) -> None:
        self.assertFalse(self.panel.duplicated(["geo", "year"]).any())
        self.assertEqual(int(self.panel["year"].min()), YEAR_MIN)
        self.assertEqual(int(self.panel["year"].max()), YEAR_MAX)
        self.assertEqual(int(self.panel.loc[self.panel["is_eu27"], "geo"].nunique()), 27)
        self.assertEqual(int(self.panel.loc[self.panel["is_big6"], "geo"].nunique()), 6)

    def test_georgia_not_folded_into_germany(self) -> None:
        de_rows = self.panel[self.panel["geo"] == "DE"]
        ge_rows = self.panel[self.panel["geo"] == "GE"]
        self.assertEqual(len(de_rows), YEAR_MAX - YEAR_MIN + 1)
        self.assertEqual(len(ge_rows), YEAR_MAX - YEAR_MIN + 1)
        self.assertNotEqual(float(de_rows["gas_retailers"].iloc[-1]), float(ge_rows["gas_retailers"].iloc[-1]))

    def test_germany_2013_and_2023_unit_checks(self) -> None:
        de = self.panel[self.panel["geo"] == "DE"].set_index("year")
        self.assertAlmostEqual(float(de.loc[2013, "e_cap_share"]), 67.0, places=2)
        self.assertAlmostEqual(float(de.loc[2013, "e_gen_share"]), 74.0, places=2)
        self.assertAlmostEqual(float(de.loc[2023, "e_gen_share"]), 57.1, places=2)
        self.assertAlmostEqual(float(de.loc[2013, "gas_retailers"]), 825.0, places=2)
        self.assertAlmostEqual(float(de.loc[2023, "gas_retailers"]), 973.0, places=2)
        self.assertAlmostEqual(float(de.loc[2023, "gas_retail_share_ge5"]), 13.3, places=2)
        self.assertGreater(float(de.loc[2023, "ren_elec_pct"]), 50.0)
        self.assertGreater(float(de.loc[2023, "elec_price_eur_kwh"]), 0.35)
        self.assertGreater(float(de.loc[2023, "unable_warm_lowinc_pct"]), float(de.loc[2023, "unable_warm_total_pct"]))

    def test_exact_log_decomposition_identity(self) -> None:
        decomp = decompose_retailer_density(self.panel, "DE")
        self.assertEqual(len(decomp), 4)
        for row in decomp.itertuples(index=False):
            self.assertAlmostEqual(
                row.log_chg_numerator_entry + row.log_chg_denominator_demand,
                row.log_chg_total,
                places=10,
            )
            self.assertAlmostEqual(
                row.share_from_numerator_pct + row.share_from_denominator_pct,
                100.0,
                places=6,
            )
        # Crisis shock (2021-2023) must be >100% denominator-driven (retailers declined while density rose)
        crisis = decomp[decomp["period"] == "Energy crisis shock (2021-2023)"].iloc[0]
        self.assertLess(float(crisis["retailers_pct_chg"]), 0.0)
        self.assertGreater(float(crisis["density_pct_chg"]), 20.0)
        self.assertGreater(float(crisis["share_from_denominator_pct"]), 100.0)

    def test_balanced_eu27_cohort_is_constant(self) -> None:
        bal = balanced_cohort(self.panel, "e_gen_share", eu27_only=True)
        yearly_counts = bal.groupby("year")["geo"].nunique()
        self.assertEqual(yearly_counts.nunique(), 1)
        self.assertGreaterEqual(int(yearly_counts.iloc[0]), 25)

    def test_twfe_strict_loo_gate(self) -> None:
        mdf = self.res["models_df"].set_index("model_id")
        self.assertTrue(bool(mdf.loc["m1_ren_to_deconc_all", "passes_strict_gate"]))
        self.assertTrue(bool(mdf.loc["m2_ren_to_deconc_eu27", "passes_strict_gate"]))
        self.assertTrue(bool(mdf.loc["m3_conc_to_elec_pps", "passes_strict_gate"]))
        self.assertFalse(bool(mdf.loc["m7_legacy_rq3_density", "passes_strict_gate"]))
        self.assertLess(float(mdf.loc["m1_ren_to_deconc_all", "coef"]), 0.0)
        self.assertGreater(float(mdf.loc["m3_conc_to_elec_pps", "coef"]), 0.0)

    def test_provenance_manifest_hashes_match_disk(self) -> None:
        self.assertTrue(MANIFEST_PATH.exists())
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        proc_path = MANIFEST_PATH.parent.parent / manifest["processed_panel"]["file"]
        self.assertEqual(sha256_file(proc_path), manifest["processed_panel"]["sha256"])
        self.assertGreaterEqual(len(manifest["sources"]), 8)

    def test_generated_deliverables_exist(self) -> None:
        self.assertTrue((OUTPUTS / "RESULTS.md").exists())
        self.assertTrue((PAPER / "generated_macros.tex").exists())
        self.assertTrue((PAPER_TABLES / "table_gas_decomposition.tex").exists())
        self.assertTrue((PAPER_TABLES / "table_big6_2023.tex").exists())
        self.assertTrue((PAPER_TABLES / "table_twfe_models.tex").exists())
        self.assertTrue((DOCS / "index.html").exists())
        self.assertGreaterEqual(len(list(FIGURES.glob("*.png"))), 5)
        # Ensure zero NaN strings leaked into generated LaTeX macros
        macro_text = (PAPER / "generated_macros.tex").read_text(encoding="utf-8")
        self.assertNotIn("nan", macro_text.lower())

    def test_sql_47_column_positional_alignment(self) -> None:
        csv_cols = list(self.panel.columns)
        self.assertEqual(len(csv_cols), 47)

        def _extract_ddl_cols(sql_path: str) -> list[str]:
            text = (ROOT / sql_path).read_text(encoding="utf-8")
            body = re.search(r"CREATE TABLE IF NOT EXISTS\s+\w+\s*\((.*)\);", text, re.S)
            self.assertIsNotNone(body, f"Missing CREATE TABLE in {sql_path}")
            cols = []
            for line in body.group(1).splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("--") or stripped.upper().startswith("PRIMARY KEY"):
                    continue
                cols.append(stripped.split()[0])
            return cols

        final_cols = _extract_ddl_cols("sql/01_create_master_panel.sql")
        staging_cols = _extract_ddl_cols("sql/02_create_staging_table.sql")
        self.assertEqual(final_cols, csv_cols)
        self.assertEqual(staging_cols, csv_cols)

        t_text = (ROOT / "sql/04_transform_staging_to_master.sql").read_text(encoding="utf-8")
        ins_match = re.search(r"INSERT INTO\s+germany_energiewende\.master_panel\s*\((.*?)\)\s*SELECT", t_text, re.S)
        self.assertIsNotNone(ins_match)
        ins_cols = [c.strip().rstrip(",") for c in ins_match.group(1).splitlines() if c.strip()]
        self.assertEqual(ins_cols, csv_cols)

        sel_match = re.search(r"\)\s*SELECT\s+(.*?)\s+FROM\s+germany_energiewende\.master_panel_staging;", t_text, re.S)
        self.assertIsNotNone(sel_match)
        # Verify every column appears in the SELECT list in exact order
        sel_text = sel_match.group(1)
        last_pos = -1
        for col in csv_cols:
            m = re.search(rf"\b{re.escape(col)}\b", sel_text[last_pos + 1 :])
            self.assertIsNotNone(m, f"Column {col} missing or out of order in sql/04 SELECT")
            last_pos += 1 + m.start()

    def test_no_personal_paths_or_credentials_in_r_and_sql(self) -> None:
        forbidden = ("C:/Users/", "C:\\Users\\", "OneDrive", "PASSWORD=", "mysql://")
        paths = list((ROOT / "R").glob("*.R")) + list((ROOT / "sql").glob("*.sql"))
        self.assertGreaterEqual(len(paths), 9)
        for p in paths:
            content = p.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, content, f"Forbidden token {token!r} found in {p.name}")

    def test_sql_five_headline_queries_recalculation(self) -> None:
        de = self.panel[self.panel["geo"] == "DE"].set_index("year")
        # Query 1: Germany transition 2013 -> 2019 -> 2023
        self.assertAlmostEqual(float(de.loc[2023, "ren_elec_pct"] - de.loc[2013, "ren_elec_pct"]), 26.661, places=3)
        self.assertAlmostEqual(float(de.loc[2023, "e_gen_share"] - de.loc[2013, "e_gen_share"]), -16.900, places=3)
        self.assertAlmostEqual(
            100.0 * float(de.loc[2023, "elec_price_eur_kwh"] - de.loc[2013, "elec_price_eur_kwh"]) / float(de.loc[2013, "elec_price_eur_kwh"]),
            39.47,
            places=2,
        )
        # Query 2: 2023 benchmark sensitivity (All N=35, EU-27 N=27, Big-6 N=6)
        p23 = self.panel[(self.panel["year"] == 2023) & (self.panel["e_gen_share"].notna())]
        self.assertEqual(len(p23), 35)
        self.assertAlmostEqual(57.1 - float(p23["e_gen_share"].median()), -6.255, places=3)
        eu23 = p23[p23["is_eu27"]]
        self.assertEqual(len(eu23), 27)
        self.assertAlmostEqual(57.1 - float(eu23["e_gen_share"].median()), -2.340, places=3)
        b6 = p23[p23["is_big6"]]
        self.assertEqual(len(b6), 6)
        self.assertAlmostEqual(57.1 - float(b6["e_gen_share"].median()), 14.955, places=3)
        # Query 3: Gas-retailer density denominator effect (2021-2023)
        self.assertAlmostEqual(
            100.0 * float(de.loc[2023, "gas_retailers"] - de.loc[2021, "gas_retailers"]) / float(de.loc[2021, "gas_retailers"]),
            -0.61,
            places=2,
        )
        self.assertAlmostEqual(
            100.0 * float(de.loc[2023, "gas_fc_twh"] - de.loc[2021, "gas_fc_twh"]) / float(de.loc[2021, "gas_fc_twh"]),
            -20.91,
            places=2,
        )
        self.assertAlmostEqual(
            100.0 * float(de.loc[2023, "retailers_per_twh"] - de.loc[2021, "retailers_per_twh"]) / float(de.loc[2021, "retailers_per_twh"]),
            25.66,
            places=2,
        )
        # Query 4: Electricity price decomposition (2021-2023)
        self.assertAlmostEqual(
            100.0 * float(de.loc[2023, "elec_price_eur_kwh"] - de.loc[2021, "elec_price_eur_kwh"]) / float(de.loc[2021, "elec_price_eur_kwh"]),
            26.73,
            places=2,
        )
        self.assertAlmostEqual(
            100.0 * float(de.loc[2023, "elec_price_extax_eur_kwh"] - de.loc[2021, "elec_price_extax_eur_kwh"]) / float(de.loc[2021, "elec_price_extax_eur_kwh"]),
            85.40,
            places=2,
        )
        self.assertAlmostEqual(
            float(de.loc[2023, "elec_price_tax_share_pct"] - de.loc[2021, "elec_price_tax_share_pct"]),
            -22.748,
            places=2,
        )
        # Query 5: Social resilience stress test (2021-2023 direct low-income vs total gaps)
        self.assertAlmostEqual(float(de.loc[2023, "unable_warm_total_pct"] - de.loc[2021, "unable_warm_total_pct"]), 4.9, places=3)
        self.assertAlmostEqual(float(de.loc[2023, "unable_warm_lowinc_pct"] - de.loc[2021, "unable_warm_lowinc_pct"]), 6.5, places=3)
        self.assertAlmostEqual(float(de.loc[2023, "unable_warm_lowinc_pct"] - de.loc[2023, "unable_warm_total_pct"]), 6.1, places=3)
        self.assertAlmostEqual(float(de.loc[2023, "utility_arrears_total_pct"] - de.loc[2021, "utility_arrears_total_pct"]), 1.7, places=3)
        self.assertAlmostEqual(float(de.loc[2023, "utility_arrears_lowinc_pct"] - de.loc[2021, "utility_arrears_lowinc_pct"]), 2.8, places=3)
        self.assertAlmostEqual(float(de.loc[2023, "utility_arrears_lowinc_pct"] - de.loc[2023, "utility_arrears_total_pct"]), 3.9, places=3)

    def test_tableau_views_and_readme_links(self) -> None:
        views_sql = (ROOT / "sql/07_tableau_views.sql").read_text(encoding="utf-8")
        expected_views = (
            "vw_tableau_de_transition",
            "vw_tableau_concentration_benchmark",
            "vw_tableau_affordability_stress",
            "vw_tableau_social_resilience",
            "vw_tableau_gas_density_caution",
        )
        for v in expected_views:
            self.assertIn(f"CREATE OR REPLACE VIEW germany_energiewende.{v}", views_sql)

        self.assertTrue((ROOT / "assets/energiewende_executive_dashboard.png").exists())
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for target in re.findall(r"\]\(([^)]+)\)", readme):
            if target.startswith(("http://", "https://", "#")):
                continue
            self.assertTrue((ROOT / target).exists(), f"Broken README relative link: {target}")


if __name__ == "__main__":
    unittest.main()
