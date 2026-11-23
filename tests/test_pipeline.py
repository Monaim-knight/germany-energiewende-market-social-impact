"""Automated data contracts, mathematical identities, and analytical integrity tests.

Compatible with both stdlib `python -m unittest` and `pytest`.
"""

from __future__ import annotations

import json
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


if __name__ == "__main__":
    unittest.main()
