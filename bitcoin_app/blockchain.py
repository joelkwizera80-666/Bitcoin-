"""A minimal educational blockchain with SHA-256 Proof-of-Work mining.

This mirrors, in miniature, how Bitcoin secures blocks: each block commits to
the previous block's hash and a nonce is searched until the block's
double-SHA-256 hash meets a difficulty target (a required number of leading
zero hex digits). It is intentionally simple and is not a real Bitcoin node.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import List, Optional


def sha256d(data: bytes) -> bytes:
    """Bitcoin's double SHA-256: ``SHA256(SHA256(data))``."""
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def target_prefix(difficulty: int) -> str:
    """The hex-hash prefix a valid block hash must start with."""
    if difficulty < 0:
        raise ValueError("difficulty must be non-negative")
    return "0" * difficulty


@dataclass
class Block:
    index: int
    data: str
    previous_hash: str
    difficulty: int
    timestamp: float = field(default_factory=time.time)
    nonce: int = 0

    def header(self) -> bytes:
        """Serialize the fields the hash commits to (nonce included)."""
        parts = [
            str(self.index),
            self.previous_hash,
            f"{self.timestamp:.6f}",
            self.data,
            str(self.difficulty),
            str(self.nonce),
        ]
        return "|".join(parts).encode("utf-8")

    def hash_hex(self) -> str:
        """The block's double-SHA-256 hash as a hex string."""
        return sha256d(self.header()).hex()

    def is_valid_pow(self) -> bool:
        return self.hash_hex().startswith(target_prefix(self.difficulty))


@dataclass
class MiningResult:
    block: Block
    hash_hex: str
    nonce: int
    difficulty: int
    hashes: int
    elapsed_s: float

    @property
    def hashrate(self) -> float:
        return self.hashes / self.elapsed_s if self.elapsed_s > 0 else float(self.hashes)


def mine_block(block: Block, max_nonce: Optional[int] = None) -> MiningResult:
    """Search for a nonce so ``block``'s hash meets its difficulty target.

    Mutates ``block.nonce`` to the winning value. Raises ``RuntimeError`` if
    ``max_nonce`` is reached without a solution.
    """
    prefix = target_prefix(block.difficulty)
    start = time.perf_counter()
    nonce = 0
    while True:
        block.nonce = nonce
        digest = block.hash_hex()
        if digest.startswith(prefix):
            elapsed = time.perf_counter() - start
            return MiningResult(
                block=block,
                hash_hex=digest,
                nonce=nonce,
                difficulty=block.difficulty,
                hashes=nonce + 1,
                elapsed_s=elapsed,
            )
        nonce += 1
        if max_nonce is not None and nonce > max_nonce:
            raise RuntimeError(
                f"no solution found within {max_nonce} nonces at difficulty {block.difficulty}"
            )


class Blockchain:
    """An in-memory chain of mined blocks."""

    def __init__(self, difficulty: int = 4):
        self.difficulty = difficulty
        self.blocks: List[Block] = []
        self._add_genesis()

    def _add_genesis(self) -> MiningResult:
        genesis = Block(
            index=0,
            data="genesis",
            previous_hash="0" * 64,
            difficulty=self.difficulty,
        )
        result = mine_block(genesis)
        self.blocks.append(genesis)
        return result

    @property
    def last_block(self) -> Block:
        return self.blocks[-1]

    def add_block(self, data: str, difficulty: Optional[int] = None) -> MiningResult:
        """Mine and append a new block carrying ``data``."""
        block = Block(
            index=self.last_block.index + 1,
            data=data,
            previous_hash=self.last_block.hash_hex(),
            difficulty=self.difficulty if difficulty is None else difficulty,
        )
        result = mine_block(block)
        self.blocks.append(block)
        return result

    def is_valid(self) -> bool:
        """Verify links and proof-of-work across the whole chain."""
        for i, block in enumerate(self.blocks):
            if not block.is_valid_pow():
                return False
            if i == 0:
                if block.previous_hash != "0" * 64:
                    return False
            elif block.previous_hash != self.blocks[i - 1].hash_hex():
                return False
        return True
