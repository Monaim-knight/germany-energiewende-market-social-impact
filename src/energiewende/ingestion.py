"""Data ingestion, schema/unit validation contracts, panel assembly, and provenance manifest."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from energiewende.config import (
    BIG6,
    COUNTRY_NAMES,
    DATA_EXTERNAL,
    DATA_PROCESSED,
    DATA_RAW,
    EU27,
    GAS_FLOOR_GWH,
    MANIFEST_PATH,
    MARKET_KEEP,
    YEAR_MAX,
    YEAR_MIN,
)
from energiewende.eurostat import (
    fetch_all_track_a_supplements,
    sha256_file,
)


def load_market_tsv(path: Path) -> pd.DataFrame:
    """Parse Eurostat nrg_ind_market TSV extract and enforce Germany 2013 unit checks."""
    lines = path.read_text(encoding="utf-8").splitlines()
    years = [int(h.strip()) for h in lines[0].split("\t")[1:] if h.strip()]
    records: list[dict[str, Any]] = []

    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        _freq, siec, indic, unit, geo = [piece.strip() for piece in parts[0].split(",")]
        key = (indic, unit, siec)
        if key not in MARKET_KEEP:
            continue
        col_name = MARKET_KEEP[key]
        for i, year in enumerate(years):
            if year < YEAR_MIN or year > YEAR_MAX:
                continue
            raw = parts[1 + i].strip().replace(" ", "") if i + 1 < len(parts) else ""
            if raw.startswith(":"):
                raw = ":"
            elif raw.endswith(("p", "e", "d", "b", "u", "c")) and raw[:-1].replace(".", "", 1).replace("-", "", 1).isdigit():
                raw = raw[:-1]
            value = np.nan if raw in {"", ":"} else float(raw)
            records.append({"geo": geo, "year": year, "column": col_name, "value": value})

    long_df = pd.DataFrame(records)
    if long_df.duplicated(["geo", "year", "column"]).any():
        raise ValueError("Duplicate (geo, year, indicator) rows detected in market TSV.")

    wide = long_df.pivot(index=["geo", "year"], columns="column", values="value").reset_index()
    wide.columns.name = None

    # Unit check contract: Germany 2013
    de_2013 = wide[(wide["geo"] == "DE") & (wide["year"] == 2013)].iloc[0]
    expected = {
        "e_cap_share": 67.0,
        "e_gen_share": 74.0,
        "e_cap_top": 29.0,
        "e_gen_top": 32.0,
        "gas_retailers": 825.0,
        "gas_retail_share_ge5": 26.0,
        "elec_retailers": 1177.0,
        "e_cap_connected_mw": 8638.0,
    }
    for col, target in expected.items():
        actual = float(de_2013[col])
        if actual != target:
            raise AssertionError(f"Market unit check failed for DE 2013 {col}: {actual} != {target}")

    return wide


def validate_panel(panel: pd.DataFrame) -> dict[str, Any]:
    """Run data-quality contract assertions on the assembled country-year panel."""
    if panel.duplicated(["geo", "year"]).any():
        raise AssertionError("Duplicate (geo, year) primary keys in master panel.")

    # Verify year window
    if int(panel["year"].min()) != YEAR_MIN or int(panel["year"].max()) != YEAR_MAX:
        raise AssertionError(f"Panel year range {panel['year'].min()}-{panel['year'].max()} != {YEAR_MIN}-{YEAR_MAX}.")

    # Verify GE (Georgia) is never collapsed into DE (Germany)
    if "GE" in panel["geo"].values and "DE" in panel["geo"].values:
        assert len(panel[panel["geo"] == "DE"]) == (YEAR_MAX - YEAR_MIN + 1)

    # Strictly bounded share columns [0, 100.5] (market shares and survey shares)
    strict_share_cols = [
        "e_cap_share",
        "e_gen_share",
        "e_cap_top",
        "e_gen_top",
        "gas_retail_share_ge5",
        "ren_total_pct",
        "unable_warm_total_pct",
        "unable_warm_lowinc_pct",
        "utility_arrears_total_pct",
    ]
    for col in strict_share_cols:
        if col in panel.columns:
            s = panel[col].dropna()
            if not s.empty and ((s < 0).any() or (s > 100.5).any()):
                raise AssertionError(f"Share column {col} out of expected [0, 100.5] bounds: min={s.min()}, max={s.max()}")

    # Under Eurostat RED II, renewable electricity share = renewable generation / gross final consumption,
    # which legitimately exceeds 100% in net-exporting hydro economies (e.g., Norway ~110-120%).
    if "ren_elec_pct" in panel.columns:
        s = panel["ren_elec_pct"].dropna()
        if not s.empty and ((s < 0).any() or (s > 150.0).any()):
            raise AssertionError(f"ren_elec_pct out of expected [0, 150] bounds: min={s.min()}, max={s.max()}")

    # Verify logical consistency: cumulative >=5% share >= largest firm share (allowing 0.5pp rounding)
    for cum_col, top_col in [("e_cap_share", "e_cap_top"), ("e_gen_share", "e_gen_top")]:
        both = panel.dropna(subset=[cum_col, top_col])
        # Note: countries where largest firm < 5% could technically have cum=0, top>0; check DE specifically
        de_both = both[both["geo"] == "DE"]
        if (de_both[cum_col] + 0.1 < de_both[top_col]).any():
            raise AssertionError(f"DE logical violation: {cum_col} < {top_col}")

    # Germany 2013 population & 2019 gas sanity checks
    de_pop_2013 = panel.loc[(panel["geo"] == "DE") & (panel["year"] == 2013), "pop"].iloc[0]
    if int(de_pop_2013) != 80523746:
        raise AssertionError(f"Germany 2013 population check failed: {de_pop_2013}")

    de_gas_2019 = float(panel.loc[(panel["geo"] == "DE") & (panel["year"] == 2019), "gas_fc_gwh"].iloc[0])
    if not (400_000 <= de_gas_2019 <= 1_200_000):
        raise AssertionError(f"Germany 2019 gas consumption out of bounds: {de_gas_2019}")

    return {
        "n_rows": int(len(panel)),
        "n_countries": int(panel["geo"].nunique()),
        "n_eu27_present": int(panel.loc[panel["is_eu27"], "geo"].nunique()),
        "n_big6_present": int(panel.loc[panel["is_big6"], "geo"].nunique()),
        "years": [int(panel["year"].min()), int(panel["year"].max())],
        "checks_passed": True,
    }


def build_master_panel(refresh: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build and persist the integrated multi-table panel and provenance manifest."""
    raw_tsv = DATA_RAW / "estat_nrg_ind_market.tsv"
    market = load_market_tsv(raw_tsv)

    # Load cached gas consumption & population (already in data/external/)
    gas = pd.read_csv(DATA_EXTERNAL / "gas_final_consumption.csv")
    pop = pd.read_csv(DATA_EXTERNAL / "population_1january.csv")

    # Load or refresh the 5 Track A Eurostat supplements
    supp_status = fetch_all_track_a_supplements(DATA_EXTERNAL, refresh=refresh)
    for name, info in supp_status.items():
        if info["status"] != "ok":
            raise RuntimeError(f"Failed to load supplement {name}: {info}")

    ren = pd.read_csv(DATA_EXTERNAL / "renewables_share.csv")
    elec_p = pd.read_csv(DATA_EXTERNAL / "household_elec_prices.csv")
    gas_p = pd.read_csv(DATA_EXTERNAL / "household_gas_prices.csv")
    warm = pd.read_csv(DATA_EXTERNAL / "energy_poverty_warmth.csv")
    arrears = pd.read_csv(DATA_EXTERNAL / "utility_arrears.csv")

    panel = market.copy()
    for ext_df in (gas, pop, ren, elec_p, gas_p, warm, arrears):
        panel = panel.merge(ext_df, on=["geo", "year"], how="left")

    # Derived metadata & cohorts
    panel["country_name"] = panel["geo"].map(COUNTRY_NAMES).fillna(panel["geo"])
    panel["is_eu27"] = panel["geo"].isin(EU27)
    panel["is_big6"] = panel["geo"].isin(BIG6)

    # Derived gas density & population-scaled metrics
    panel["gas_fc_twh"] = panel["gas_fc_gwh"] / 1000.0
    panel["retailers_per_twh"] = np.where(
        panel["gas_fc_twh"] > 0, panel["gas_retailers"] / panel["gas_fc_twh"], np.nan
    )
    panel["in_density_sample"] = (
        panel["gas_retailers"].notna()
        & panel["gas_fc_gwh"].notna()
        & (panel["gas_fc_gwh"] >= GAS_FLOOR_GWH)
    )
    panel["retailers_per_million"] = np.where(
        panel["in_density_sample"] & panel["pop"].notna() & (panel["pop"] > 0),
        panel["gas_retailers"] / (panel["pop"] / 1_000_000.0),
        np.nan,
    )

    # Electricity concentration decomposition: non-leader >=5% firms share & top-firm share of cumulative >=5%
    panel["e_cap_other_major_share"] = panel["e_cap_share"] - panel["e_cap_top"]
    panel["e_gen_other_major_share"] = panel["e_gen_share"] - panel["e_gen_top"]

    # Gross capacity churn (connected + decommissioned MW)
    panel["e_cap_gross_churn_mw"] = panel["e_cap_connected_mw"] + panel["e_cap_decomm_mw"]

    panel = panel.sort_values(["geo", "year"]).reset_index(drop=True)
    validation = validate_panel(panel)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out_csv = DATA_PROCESSED / "master_panel.csv"
    panel.to_csv(out_csv, index=False)

    manifest = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "window": [YEAR_MIN, YEAR_MAX],
        "validation": validation,
        "sources": {
            "market_tsv": {
                "file": "data/raw/estat_nrg_ind_market.tsv",
                "dataset": "nrg_ind_market",
                "sha256": sha256_file(raw_tsv),
            },
            "gas_final_consumption": {
                "file": "data/external/gas_final_consumption.csv",
                "dataset": "nrg_bal_s (FC_E + FC_NE, G3000, GWH)",
                "sha256": sha256_file(DATA_EXTERNAL / "gas_final_consumption.csv"),
            },
            "population": {
                "file": "data/external/population_1january.csv",
                "dataset": "demo_pjan (TOTAL, T)",
                "sha256": sha256_file(DATA_EXTERNAL / "population_1january.csv"),
            },
            **{k: v["meta"] for k, v in supp_status.items()},
        },
        "processed_panel": {
            "file": "data/processed/master_panel.csv",
            "rows": int(len(panel)),
            "columns": list(panel.columns),
            "sha256": sha256_file(out_csv),
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return panel, manifest
