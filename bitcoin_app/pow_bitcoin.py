"""Bitcoin-accurate Proof-of-Work primitives.

Unlike the simplified hex-prefix miner in ``blockchain.py``, this module models
the real consensus rules:

* an 80-byte block header (version, prev block hash, merkle root, time, bits,
  nonce), all little-endian;
* the compact ``nBits`` difficulty encoding and its 256-bit target;
* a block hash that is ``SHA256d`` of the header interpreted as a little-endian
  integer, valid when ``hash <= target``;
* Merkle roots built from transaction ids with the odd-node duplication rule.

Correctness is pinned by reproducing Bitcoin's genesis block hash in the tests.

Byte-order note: hashes are handled in *internal* (little-endian) byte order
inside this module. Human-facing hex (block explorers) is big-endian, i.e. the
internal bytes reversed. Use the ``*_hex`` helpers for display order and the
``from_hex`` helpers to parse display order.
"""

from __future__ import annotations

import hashlib
import struct
import time
from dataclasses import dataclass, field
from typing import List, Optional


def sha256d(data: bytes) -> bytes:
    """Double SHA-256 (internal byte order)."""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def bits_to_target(bits: int) -> int:
    """Decode the compact ``nBits`` representation into a 256-bit target."""
    exponent = bits >> 24
    mantissa = bits & 0x007FFFFF
    if exponent <= 3:
        return mantissa >> (8 * (3 - exponent))
    return mantissa << (8 * (exponent - 3))


def target_to_bits(target: int) -> int:
    """Encode a target as the compact ``nBits`` representation."""
    if target == 0:
        return 0
    size = (target.bit_length() + 7) // 8
    if size <= 3:
        mantissa = target << (8 * (3 - size))
    else:
        mantissa = target >> (8 * (size - 3))
    # The mantissa is signed; if the high bit is set, shift down one byte.
    if mantissa & 0x00800000:
        mantissa >>= 8
        size += 1
    return (size << 24) | mantissa


# The difficulty-1 target (bits 0x1d00ffff), used to express relative difficulty.
DIFFICULTY_1_TARGET = bits_to_target(0x1D00FFFF)
MAX_TARGET = DIFFICULTY_1_TARGET


def target_to_difficulty(target: int) -> float:
    """Bitcoin's relative difficulty: difficulty-1 target divided by ``target``."""
    return DIFFICULTY_1_TARGET / target


def target_from_leading_zero_bits(zero_bits: int) -> int:
    """A convenience target with ``zero_bits`` leading zero bits (2**(256-n) - 1)."""
    if not 0 <= zero_bits <= 256:
        raise ValueError("zero_bits must be in 0..256")
    return (1 << (256 - zero_bits)) - 1


def compute_merkle_root(txids: List[bytes]) -> bytes:
    """Merkle root (internal byte order) from txids in internal byte order.

    Odd layers duplicate the final hash, matching Bitcoin consensus.
    """
    if not txids:
        raise ValueError("at least one txid is required")
    layer = list(txids)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [sha256d(layer[i] + layer[i + 1]) for i in range(0, len(layer), 2)]
    return layer[0]


def txid_from_raw(raw_tx: bytes) -> bytes:
    """A transaction id (internal byte order) is ``SHA256d`` of its raw bytes."""
    return sha256d(raw_tx)


def _rev_hex(h: str) -> bytes:
    """Parse a display-order (big-endian) hex string to internal bytes."""
    return bytes.fromhex(h)[::-1]


@dataclass
class BlockHeader:
    version: int
    prev_hash: bytes  # internal (little-endian) byte order, 32 bytes
    merkle_root: bytes  # internal (little-endian) byte order, 32 bytes
    bits: int
    timestamp: int = field(default_factory=lambda: int(time.time()))
    nonce: int = 0

    def __post_init__(self) -> None:
        if len(self.prev_hash) != 32:
            raise ValueError("prev_hash must be 32 bytes (internal order)")
        if len(self.merkle_root) != 32:
            raise ValueError("merkle_root must be 32 bytes (internal order)")

    @classmethod
    def from_hex(
        cls,
        version: int,
        prev_hash_hex: str,
        merkle_root_hex: str,
        bits: int,
        timestamp: int,
        nonce: int = 0,
    ) -> "BlockHeader":
        """Build a header from display-order (big-endian) hex hashes."""
        return cls(
            version=version,
            prev_hash=_rev_hex(prev_hash_hex),
            merkle_root=_rev_hex(merkle_root_hex),
            bits=bits,
            timestamp=timestamp,
            nonce=nonce,
        )

    def serialize(self) -> bytes:
        """The canonical 80-byte header."""
        return (
            struct.pack("<I", self.version)
            + self.prev_hash
            + self.merkle_root
            + struct.pack("<I", self.timestamp)
            + struct.pack("<I", self.bits)
            + struct.pack("<I", self.nonce)
        )

    def hash(self) -> bytes:
        """Block hash in internal (little-endian) byte order."""
        return sha256d(self.serialize())

    def hash_hex(self) -> str:
        """Block hash in display (big-endian) order, as shown by explorers."""
        return self.hash()[::-1].hex()

    def target(self) -> int:
        return bits_to_target(self.bits)

    def difficulty(self) -> float:
        return target_to_difficulty(self.target())

    def is_valid_pow(self) -> bool:
        """True when the hash, as a little-endian integer, is <= the target."""
        return int.from_bytes(self.hash(), "little") <= self.target()


@dataclass
class MiningResult:
    header: BlockHeader
    hash_hex: str
    nonce: int
    hashes: int
    elapsed_s: float
    target: int

    @property
    def hashrate(self) -> float:
        return self.hashes / self.elapsed_s if self.elapsed_s > 0 else float(self.hashes)

    @property
    def difficulty(self) -> float:
        return target_to_difficulty(self.target)


def mine(header: BlockHeader, max_nonce: int = 0xFFFFFFFF) -> MiningResult:
    """Search nonces (0..max_nonce) until ``header``'s hash meets its target.

    Mutates ``header.nonce`` to the winning value. Raises ``RuntimeError`` if no
    nonce in range satisfies the target (real miners then roll other fields).
    """
    target = header.target()
    start = time.perf_counter()
    for nonce in range(0, max_nonce + 1):
        header.nonce = nonce
        if int.from_bytes(header.hash(), "little") <= target:
            elapsed = time.perf_counter() - start
            return MiningResult(
                header=header,
                hash_hex=header.hash_hex(),
                nonce=nonce,
                hashes=nonce + 1,
                elapsed_s=elapsed,
                target=target,
            )
    raise RuntimeError(
        f"no nonce in 0..{max_nonce} satisfied target for bits {header.bits:#010x}"
    )
