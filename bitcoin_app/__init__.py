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
from .blockchain import (
    sha256d,
    target_prefix,
    Block,
    Blockchain,
    MiningResult,
    mine_block,
)
from .pow_bitcoin import (
    bits_to_target,
    target_to_bits,
    target_to_difficulty,
    target_from_leading_zero_bits,
    compute_merkle_root,
    txid_from_raw,
    BlockHeader,
    DIFFICULTY_1_TARGET,
    MAX_TARGET,
    mine as mine_header,
    MiningResult as HeaderMiningResult,
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
    "sha256d",
    "target_prefix",
    "Block",
    "Blockchain",
    "MiningResult",
    "mine_block",
    "bits_to_target",
    "target_to_bits",
    "target_to_difficulty",
    "target_from_leading_zero_bits",
    "compute_merkle_root",
    "txid_from_raw",
    "BlockHeader",
    "DIFFICULTY_1_TARGET",
    "MAX_TARGET",
    "mine_header",
    "HeaderMiningResult",
    "__version__",
]
