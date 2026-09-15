"""Tests for the Bitcoin-accurate Proof-of-Work module.

The genesis-block tests are the correctness anchor: if header serialization,
the nBits target, double-SHA-256, byte order, or the Merkle rule were wrong,
the well-known genesis hash would not reproduce.
"""

import pytest

from bitcoin_app import (
    bits_to_target,
    target_to_bits,
    target_to_difficulty,
    target_from_leading_zero_bits,
    compute_merkle_root,
    txid_from_raw,
    BlockHeader,
    mine_header,
    DIFFICULTY_1_TARGET,
)

GENESIS_MERKLE_ROOT = "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b"
GENESIS_HASH = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
GENESIS_COINBASE_RAW = (
    "01000000010000000000000000000000000000000000000000000000000000000000000000"
    "ffffffff4d04ffff001d0104455468652054696d65732030332f4a616e2f3230303920436861"
    "6e63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f757420666f72"
    "2062616e6b73ffffffff0100f2052a01000000434104678afdb0fe5548271967f1a67130b710"
    "5cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b"
    "8d578a4c702b6bf11d5fac00000000"
)


def test_nbits_target_roundtrip():
    assert target_to_bits(bits_to_target(0x1D00FFFF)) == 0x1D00FFFF
    assert target_to_bits(bits_to_target(0x1B0404CB)) == 0x1B0404CB


def test_difficulty_one():
    assert target_to_difficulty(DIFFICULTY_1_TARGET) == pytest.approx(1.0)


def test_target_from_leading_zero_bits():
    t = target_from_leading_zero_bits(8)
    assert t == (1 << (256 - 8)) - 1
    with pytest.raises(ValueError):
        target_from_leading_zero_bits(300)


def test_genesis_merkle_root_from_coinbase():
    txid = txid_from_raw(bytes.fromhex(GENESIS_COINBASE_RAW))
    root = compute_merkle_root([txid])
    # display (big-endian) order
    assert root[::-1].hex() == GENESIS_MERKLE_ROOT


def test_genesis_block_hash_reproduces():
    header = BlockHeader.from_hex(
        version=1,
        prev_hash_hex="0" * 64,
        merkle_root_hex=GENESIS_MERKLE_ROOT,
        bits=0x1D00FFFF,
        timestamp=1231006505,
        nonce=2083236893,
    )
    assert len(header.serialize()) == 80
    assert header.hash_hex() == GENESIS_HASH
    assert header.is_valid_pow()


def test_genesis_wrong_nonce_is_invalid():
    header = BlockHeader.from_hex(
        version=1,
        prev_hash_hex="0" * 64,
        merkle_root_hex=GENESIS_MERKLE_ROOT,
        bits=0x1D00FFFF,
        timestamp=1231006505,
        nonce=2083236892,  # off by one
    )
    assert header.hash_hex() != GENESIS_HASH
    assert not header.is_valid_pow()


def test_merkle_root_odd_duplicates_last():
    a, b, c = (txid_from_raw(x) for x in (b"a", b"b", b"c"))
    import hashlib

    def d256(x):
        return hashlib.sha256(hashlib.sha256(x).digest()).digest()

    expected = d256(d256(a + b) + d256(c + c))
    assert compute_merkle_root([a, b, c]) == expected


def test_mine_produces_valid_header():
    txid = txid_from_raw(b"payload")
    root = compute_merkle_root([txid])
    bits = target_to_bits(target_from_leading_zero_bits(12))
    header = BlockHeader(version=1, prev_hash=b"\x00" * 32, merkle_root=root, bits=bits)
    result = mine_header(header)
    assert header.is_valid_pow()
    assert result.hash_hex == header.hash_hex()
    assert result.hashes == result.nonce + 1
    # low-difficulty hash should have at least ~1 leading zero hex digit
    assert result.hash_hex.startswith("0")


def test_mine_gives_up_when_no_nonce_fits():
    header = BlockHeader(
        version=1,
        prev_hash=b"\x00" * 32,
        merkle_root=b"\x11" * 32,
        bits=target_to_bits(target_from_leading_zero_bits(240)),
    )
    with pytest.raises(RuntimeError):
        mine_header(header, max_nonce=200)
