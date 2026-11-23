"""Eurostat Dissemination API v1.0 client with local caching and provenance hashing."""

from __future__ import annotations

import hashlib
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    import certifi
except ImportError:  # pragma: no cover
    certifi = None

EUROSTAT_BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def _ssl_context() -> ssl.SSLContext:
    """Create a verified TLS context using certifi when available."""
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a local file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def build_url(dataset: str, params: list[tuple[str, str]]) -> str:
    """Build Eurostat JSON-stat query URL supporting repeated keys."""
    query = urllib.parse.urlencode([("format", "JSON"), ("lang", "EN"), *params])
    return f"{EUROSTAT_BASE}/{dataset}?{query}"


def fetch_jsonstat(dataset: str, params: list[tuple[str, str]], timeout: int = 120) -> tuple[dict[str, Any], str]:
    """Fetch JSON-stat payload from Eurostat API and return (payload, url)."""
    url = build_url(dataset, params)
    req = urllib.request.Request(url, headers={"User-Agent": "energiewende-analytics/1.0"})
    with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload, url


def jsonstat_to_frame(payload: dict[str, Any], value_name: str = "value") -> pd.DataFrame:
    """Convert Eurostat JSON-stat 2.0 payload into a tidy DataFrame."""
    dim_ids: list[str] = payload["id"]
    sizes: list[int] = payload["size"]
    codes: list[list[str]] = []
    for dim_id in dim_ids:
        index = payload["dimension"][dim_id]["category"]["index"]
        if isinstance(index, dict):
            ordered: list[str] = [""] * len(index)
            for code, pos in index.items():
                ordered[int(pos)] = code
        else:
            ordered = list(index)
        codes.append(ordered)

    status = payload.get("status") or {}
    values = payload.get("value") or {}
    rows = []
    for flat_key, val in values.items():
        flat_i = int(flat_key)
        coords = []
        rem = flat_i
        for size in reversed(sizes):
            coords.append(rem % size)
            rem //= size
        coords.reverse()
        row = {dim_id: code_list[pos] for dim_id, code_list, pos in zip(dim_ids, codes, coords)}
        row[value_name] = float(val) if val is not None else np.nan
        row["status"] = status.get(str(flat_i), status.get(flat_key, ""))
        rows.append(row)
    return pd.DataFrame(rows)


def fetch_renewables(cache_path: Path, year_min: int = 2013, year_max: int = 2023, refresh: bool = False) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch Eurostat nrg_ind_ren: overall (REN) and electricity (REN_ELC) renewable shares (%)."""
    params = [
        ("freq", "A"),
        ("nrg_bal", "REN"),
        ("nrg_bal", "REN_ELC"),
        ("unit", "PC"),
        ("sinceTimePeriod", str(year_min)),
        ("untilTimePeriod", str(year_max)),
    ]
    url = build_url("nrg_ind_ren", params)
    if cache_path.exists() and not refresh:
        df = pd.read_csv(cache_path)
        meta = {"dataset": "nrg_ind_ren", "url": url, "cached": True, "rows": len(df), "sha256": sha256_file(cache_path)}
        return df, meta

    payload, url = fetch_jsonstat("nrg_ind_ren", params)
    raw = jsonstat_to_frame(payload, "value")
    raw["year"] = raw["time"].astype(int)
    wide = raw.pivot_table(index=["geo", "year"], columns="nrg_bal", values="value", aggfunc="first").reset_index()
    wide = wide.rename(columns={"REN": "ren_total_pct", "REN_ELC": "ren_elec_pct"})
    wide = wide.sort_values(["geo", "year"]).reset_index(drop=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(cache_path, index=False)
    meta = {
        "dataset": "nrg_ind_ren",
        "url": url,
        "updated": payload.get("updated", ""),
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "rows": len(wide),
        "sha256": sha256_file(cache_path),
    }
    return wide, meta


def fetch_household_prices(
    dataset: str,
    siec: str,
    nrg_cons: str,
    prefix: str,
    cache_path: Path,
    year_min: int = 2013,
    year_max: int = 2023,
    refresh: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch bi-annual household energy prices (EUR/PPS all-tax + EUR ex-tax per kWh) and aggregate to annual means."""
    params = [
        ("freq", "S"),
        ("siec", siec),
        ("nrg_cons", nrg_cons),
        ("unit", "KWH"),
        ("tax", "I_TAX"),
        ("tax", "X_TAX"),
        ("currency", "EUR"),
        ("currency", "PPS"),
        ("sinceTimePeriod", f"{year_min}-S1"),
        ("untilTimePeriod", f"{year_max}-S2"),
    ]
    url = build_url(dataset, params)
    if cache_path.exists() and not refresh:
        df = pd.read_csv(cache_path)
        meta = {"dataset": dataset, "url": url, "cached": True, "rows": len(df), "sha256": sha256_file(cache_path)}
        return df, meta

    payload, url = fetch_jsonstat(dataset, params)
    raw = jsonstat_to_frame(payload, "price")
    raw["year"] = raw["time"].str.slice(0, 4).astype(int)
    raw = raw[(raw["year"] >= year_min) & (raw["year"] <= year_max)].copy()
    annual = raw.groupby(["geo", "year", "tax", "currency"], as_index=False)["price"].mean()
    annual["col"] = annual.apply(
        lambda r: (
            f"{prefix}_eur_kwh"
            if (r["tax"] == "I_TAX" and r["currency"] == "EUR")
            else (
                f"{prefix}_pps_kwh"
                if (r["tax"] == "I_TAX" and r["currency"] == "PPS")
                else (f"{prefix}_extax_eur_kwh" if (r["tax"] == "X_TAX" and r["currency"] == "EUR") else None)
            )
        ),
        axis=1,
    )
    annual = annual.dropna(subset=["col"])
    wide = annual.pivot_table(index=["geo", "year"], columns="col", values="price", aggfunc="first").reset_index()
    if f"{prefix}_eur_kwh" in wide.columns and f"{prefix}_extax_eur_kwh" in wide.columns:
        wide[f"{prefix}_tax_share_pct"] = np.where(
            wide[f"{prefix}_eur_kwh"] > 0,
            100.0 * (wide[f"{prefix}_eur_kwh"] - wide[f"{prefix}_extax_eur_kwh"]) / wide[f"{prefix}_eur_kwh"],
            np.nan,
        )
    wide = wide.sort_values(["geo", "year"]).reset_index(drop=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(cache_path, index=False)
    meta = {
        "dataset": dataset,
        "url": url,
        "updated": payload.get("updated", ""),
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "rows": len(wide),
        "sha256": sha256_file(cache_path),
    }
    return wide, meta


def fetch_social_indicator(
    dataset: str,
    prefix: str,
    cache_path: Path,
    year_min: int = 2013,
    year_max: int = 2023,
    refresh: bool = False,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch EU-SILC social/energy-poverty indicator for TOTAL, below-60% (B_60), and above-60% (A_60) income groups."""
    params = [
        ("freq", "A"),
        ("hhcomp", "TOTAL"),
        ("rskpovth", "TOTAL"),
        ("rskpovth", "B_60"),
        ("rskpovth", "A_60"),
        ("unit", "PC"),
        ("sinceTimePeriod", str(year_min)),
        ("untilTimePeriod", str(year_max)),
    ]
    url = build_url(dataset, params)
    if cache_path.exists() and not refresh:
        df = pd.read_csv(cache_path)
        meta = {"dataset": dataset, "url": url, "cached": True, "rows": len(df), "sha256": sha256_file(cache_path)}
        return df, meta

    payload, url = fetch_jsonstat(dataset, params)
    raw = jsonstat_to_frame(payload, "value")
    raw["year"] = raw["time"].astype(int)
    wide = raw.pivot_table(index=["geo", "year"], columns="rskpovth", values="value", aggfunc="first").reset_index()
    wide = wide.rename(
        columns={
            "TOTAL": f"{prefix}_total_pct",
            "B_60": f"{prefix}_lowinc_pct",
            "A_60": f"{prefix}_above60_pct",
        }
    )
    if f"{prefix}_lowinc_pct" in wide.columns and f"{prefix}_above60_pct" in wide.columns:
        wide[f"{prefix}_income_gap_pp"] = wide[f"{prefix}_lowinc_pct"] - wide[f"{prefix}_above60_pct"]
    wide = wide.sort_values(["geo", "year"]).reset_index(drop=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(cache_path, index=False)
    meta = {
        "dataset": dataset,
        "url": url,
        "updated": payload.get("updated", ""),
        "fetched_utc": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "rows": len(wide),
        "sha256": sha256_file(cache_path),
    }
    return wide, meta


def fetch_all_track_a_supplements(external_dir: Path, refresh: bool = False) -> dict[str, Any]:
    """Download/load all Track A supplementary Eurostat datasets and return provenance metadata."""
    results: dict[str, Any] = {}
    tasks = [
        ("renewables", lambda: fetch_renewables(external_dir / "renewables_share.csv", refresh=refresh)),
        (
            "elec_prices",
            lambda: fetch_household_prices(
                "nrg_pc_204", "E7000", "KWH2500-4999", "elec_price", external_dir / "household_elec_prices.csv", refresh=refresh
            ),
        ),
        (
            "gas_prices",
            lambda: fetch_household_prices(
                "nrg_pc_202", "G3000", "GJ20-199", "gas_price", external_dir / "household_gas_prices.csv", refresh=refresh
            ),
        ),
        (
            "energy_poverty",
            lambda: fetch_social_indicator("ilc_mdes01", "unable_warm", external_dir / "energy_poverty_warmth.csv", refresh=refresh),
        ),
        (
            "utility_arrears",
            lambda: fetch_social_indicator("ilc_mdes07", "utility_arrears", external_dir / "utility_arrears.csv", refresh=refresh),
        ),
    ]
    for name, fn in tasks:
        try:
            df, meta = fn()
            results[name] = {"status": "ok", "meta": meta, "de_sample": df[df["geo"] == "DE"].tail(3).to_dict(orient="records")}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")[:300]
            results[name] = {"status": "http_error", "code": e.code, "error": body}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
    return results


if __name__ == "__main__":
    ext = Path(__file__).resolve().parents[2] / "data" / "external"
    out = fetch_all_track_a_supplements(ext, refresh=True)
    print(json.dumps(out, indent=2))
