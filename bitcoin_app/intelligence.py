"""666 Intelligence — Bitcoin chain recon for ROBIN BANKS.

Watch-only. No custody. Public mempool.space endpoints with offline fallback.
CAPTAINCOOKCRYPTO is the navigator: quote the route, never hold the haul.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import requests

from .core import SATOSHIS_PER_BTC, is_valid_address, satoshi_to_btc

MEMPOOL_BASE = "https://mempool.space/api"
DIRECTORATE = "666-INTEL"
UNIT = "CAPTAINCOOKCRYPTO"
PRODUCT = "ROBIN BANKS"
CHAIN = "bitcoin-l1"


@dataclass
class FeeChart:
    fastest: int
    half_hour: int
    hour: int
    economy: int
    minimum: int
    source: str
    live: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VaultDossier:
    address: str
    valid: bool
    chain: str = CHAIN
    funded_txo_count: int = 0
    funded_sats: int = 0
    spent_sats: int = 0
    balance_sats: int = 0
    balance_btc: str = "0.00000000"
    tx_count: int = 0
    source: str = "offline"
    live: bool = False
    classification: str = "UNVERIFIED"
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _get_json(path: str, timeout: float = 8.0) -> Optional[Any]:
    try:
        resp = requests.get(f"{MEMPOOL_BASE}{path}", timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except (requests.RequestException, ValueError):
        return None


def chart_fees(*, allow_network: bool = True) -> FeeChart:
    """Captain's fee chart — sats/vB recommended by mempool."""
    fallback = FeeChart(20, 15, 10, 5, 1, "offline", False)
    if not allow_network:
        return fallback
    data = _get_json("/v1/fees/recommended")
    if not isinstance(data, dict):
        return fallback
    try:
        return FeeChart(
            fastest=int(data.get("fastestFee", 20)),
            half_hour=int(data.get("halfHourFee", 15)),
            hour=int(data.get("hourFee", 10)),
            economy=int(data.get("economyFee", 5)),
            minimum=int(data.get("minimumFee", 1)),
            source="mempool.space",
            live=True,
        )
    except (TypeError, ValueError):
        return fallback


def classify_vault(balance_sats: int, tx_count: int, valid: bool) -> tuple[str, list[str]]:
    notes: list[str] = []
    if not valid:
        return "FOG", ["Address failed Base58Check. Do not route."]
    if tx_count == 0 and balance_sats == 0:
        notes.append("Clean watch address. No chain history.")
        return "DARK", notes
    if balance_sats == 0 and tx_count > 0:
        notes.append("Emptied vault. History exists; no remaining haul.")
        return "SPENT", notes
    if balance_sats >= SATOSHIS_PER_BTC:
        notes.append("Treasury-grade balance (>= 1 BTC).")
        return "HOLD", notes
    notes.append("Active vault with residual sats.")
    return "WATCH", notes


def recon_address(address: str, *, allow_network: bool = True) -> VaultDossier:
    """Watch-only dossier for a Bitcoin address."""
    valid = is_valid_address(address)
    dossier = VaultDossier(address=address, valid=valid)
    if not valid:
        dossier.classification, dossier.notes = classify_vault(0, 0, False)
        return dossier

    if not allow_network:
        dossier.classification, dossier.notes = classify_vault(0, 0, True)
        dossier.notes.append("Network denied. Offline classification only.")
        return dossier

    data = _get_json(f"/address/{address}")
    if not isinstance(data, dict):
        dossier.classification, dossier.notes = classify_vault(0, 0, True)
        dossier.notes.append("Mempool unreachable. Offline fallback.")
        return dossier

    chain_stats = data.get("chain_stats") or {}
    mempool_stats = data.get("mempool_stats") or {}

    funded = int(chain_stats.get("funded_txo_sum", 0)) + int(
        mempool_stats.get("funded_txo_sum", 0)
    )
    spent = int(chain_stats.get("spent_txo_sum", 0)) + int(
        mempool_stats.get("spent_txo_sum", 0)
    )
    funded_count = int(chain_stats.get("funded_txo_count", 0)) + int(
        mempool_stats.get("funded_txo_count", 0)
    )
    tx_count = int(chain_stats.get("tx_count", 0)) + int(mempool_stats.get("tx_count", 0))
    balance = funded - spent

    dossier.funded_txo_count = funded_count
    dossier.funded_sats = funded
    dossier.spent_sats = spent
    dossier.balance_sats = balance
    dossier.balance_btc = str(satoshi_to_btc(balance))
    dossier.tx_count = tx_count
    dossier.source = "mempool.space"
    dossier.live = True
    dossier.classification, dossier.notes = classify_vault(balance, tx_count, True)
    return dossier


def plot_route(
    destination: str,
    sats: int,
    vbytes: int = 140,
    *,
    allow_network: bool = True,
) -> dict[str, Any]:
    """Navigator quote: destination, haul, fee at current fastest rate."""
    if sats < 0:
        raise ValueError("sats must be >= 0")
    if vbytes <= 0:
        raise ValueError("vbytes must be > 0")

    fees = chart_fees(allow_network=allow_network)
    valid = is_valid_address(destination)
    fee_sats = fees.fastest * vbytes
    total = sats + fee_sats

    return {
        "unit": UNIT,
        "product": PRODUCT,
        "chain": CHAIN,
        "destination": destination,
        "destination_valid": valid,
        "haul_sats": sats,
        "haul_btc": str(satoshi_to_btc(sats)),
        "assumed_vbytes": vbytes,
        "fee_rate_sat_vb": fees.fastest,
        "fee_sats": fee_sats,
        "total_sats": total,
        "total_btc": str(satoshi_to_btc(total)),
        "fees": fees.as_dict(),
        "clearance": "GO" if valid and sats > 0 else "HOLD",
        "note": "Quote only. You sign on your own wallet. Intelligence holds nothing.",
    }
