"""Live Bitcoin price helper.

Fetches the current BTC price from the public CoinGecko API. Network access is
optional: callers that pass ``allow_network=False`` (or hit an error) receive a
clearly-labelled offline fallback so the app and tests never hard-fail.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

_COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
_OFFLINE_PRICE_USD = 0.0


@dataclass
class PriceQuote:
    currency: str
    price: float
    source: str
    live: bool


def get_btc_price(
    currency: str = "usd",
    *,
    allow_network: bool = True,
    timeout: float = 8.0,
) -> PriceQuote:
    """Return the current BTC price for ``currency``.

    On any network error (or when ``allow_network`` is False) returns a
    non-live fallback quote instead of raising.
    """
    currency = currency.lower()
    if not allow_network:
        return PriceQuote(currency, _OFFLINE_PRICE_USD, "offline", live=False)

    try:
        resp = requests.get(
            _COINGECKO_URL,
            params={"ids": "bitcoin", "vs_currencies": currency},
            timeout=timeout,
        )
        resp.raise_for_status()
        price = float(resp.json()["bitcoin"][currency])
        return PriceQuote(currency, price, "coingecko", live=True)
    except (requests.RequestException, KeyError, ValueError):
        return PriceQuote(currency, _OFFLINE_PRICE_USD, "offline", live=False)


def _fmt(value: float, currency: str) -> Optional[str]:
    if value <= 0:
        return None
    return f"{value:,.2f} {currency.upper()}"
