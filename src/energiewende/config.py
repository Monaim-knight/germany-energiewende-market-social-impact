"""Central configuration, peer cohorts, and pre-registered analytical thresholds."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_EXTERNAL = ROOT / "data" / "external"
DATA_PROCESSED = ROOT / "data" / "processed"
MANIFEST_PATH = ROOT / "data" / "manifest.json"
OUTPUTS = ROOT / "outputs"
TABLES = OUTPUTS / "tables"
FIGURES = OUTPUTS / "figures"
PAPER = ROOT / "paper"
PAPER_TABLES = PAPER / "tables"
DOCS = ROOT / "docs"

YEAR_MIN = 2013
YEAR_MAX = 2023

# Pre-registered decision thresholds
GAS_FLOOR_GWH = 1000.0
SHARE_FLAT_PP = 2.0
DENSITY_FLAT_REL = 0.10
LOO_BAND = 0.50
MIN_YEARS_FOR_FE = 2

# Peer cohorts (Eurostat geo codes: EL = Greece, GE = Georgia)
EU27: tuple[str, ...] = (
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL",
    "ES", "FI", "FR", "HR", "HU", "IE", "IT", "LT", "LU",
    "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK",
)

# Large interconnected European power & gas markets (for size-comparable benchmarking)
BIG6: tuple[str, ...] = ("DE", "FR", "IT", "ES", "PL", "NL")

COUNTRY_NAMES: dict[str, str] = {
    "AT": "Austria",
    "BA": "Bosnia & Herzegovina",
    "BE": "Belgium",
    "BG": "Bulgaria",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DE": "Germany",
    "DK": "Denmark",
    "EE": "Estonia",
    "EL": "Greece",
    "ES": "Spain",
    "FI": "Finland",
    "FR": "France",
    "GE": "Georgia",
    "HR": "Croatia",
    "HU": "Hungary",
    "IE": "Ireland",
    "IT": "Italy",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "MD": "Moldova",
    "ME": "Montenegro",
    "MK": "North Macedonia",
    "MT": "Malta",
    "NL": "Netherlands",
    "NO": "Norway",
    "PL": "Poland",
    "PT": "Portugal",
    "RO": "Romania",
    "RS": "Serbia",
    "SE": "Sweden",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "TR": "Turkey",
    "XK": "Kosovo",
}

# Market indicators extracted from estat_nrg_ind_market.tsv
MARKET_KEEP: dict[tuple[str, str, str], str] = {
    # Electricity generation & capacity concentration
    ("CMPY_ECAP5", "PC", "E7000"): "e_cap_share",
    ("CMPY_EG5", "PC", "E7000"): "e_gen_share",
    ("LCMPY_IECAP", "PC", "E7000"): "e_cap_top",
    ("LCMPY_EG", "PC", "E7000"): "e_gen_top",
    ("PCMPY_NEG5", "NR", "E7000"): "e_gen_firms_ge5",
    # Electricity capacity transition flows (MW)
    ("ECAP_CN", "MW", "E7000"): "e_cap_connected_mw",
    ("ECAP_DC", "MW", "E7000"): "e_cap_decomm_mw",
    ("ECAP_VAR", "MW", "E7000"): "e_cap_net_var_mw",
    # Electricity retail
    ("ERTL", "NR", "E7000"): "elec_retailers",
    # Natural gas retail & concentration
    ("GRTL", "NR", "G3000"): "gas_retailers",
    ("GRTL_NG5", "PC", "G3000"): "gas_retail_share_ge5",
    ("GRTL_SELL_NG5", "NR", "G3000"): "gas_retail_firms_ge5",
    ("CMPY_NG", "NR", "G3000"): "gas_upstream_firms",
}
