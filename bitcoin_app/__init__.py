"""Bitcoin- : a small, dependency-light Bitcoin toolkit.

Provides unit conversions, Base58Check encoding, P2PKH address validation and
generation, and a live price helper. Exposed through a CLI and a small Flask
web dashboard.
"""

from .core import (
    SATOSHIS_PER_BTC,
    btc_to_satoshi,
    satoshi_to_btc,
    hash160,
    b58check_encode,
    b58check_decode,
    pubkey_to_p2pkh_address,
    is_valid_address,
    generate_keypair,
    KeyPair,
)

__version__ = "0.1.0"

__all__ = [
    "SATOSHIS_PER_BTC",
    "btc_to_satoshi",
    "satoshi_to_btc",
    "hash160",
    "b58check_encode",
    "b58check_decode",
    "pubkey_to_p2pkh_address",
    "is_valid_address",
    "generate_keypair",
    "KeyPair",
    "__version__",
]
