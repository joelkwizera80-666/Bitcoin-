import hashlib

import pytest

from bitcoin_app import (
    sha256d,
    target_prefix,
    Block,
    Blockchain,
    mine_block,
)


def test_sha256d_matches_manual():
    data = b"hello"
    expected = hashlib.sha256(hashlib.sha256(data).digest()).digest()
    assert sha256d(data) == expected
    assert len(sha256d(data)) == 32


def test_target_prefix():
    assert target_prefix(0) == ""
    assert target_prefix(4) == "0000"
    with pytest.raises(ValueError):
        target_prefix(-1)


def test_mine_block_meets_target():
    block = Block(index=1, data="test", previous_hash="0" * 64, difficulty=3)
    result = mine_block(block)
    assert result.hash_hex.startswith("000")
    assert result.hash_hex == block.hash_hex()
    assert block.is_valid_pow()
    assert result.nonce == block.nonce
    assert result.hashes == result.nonce + 1


def test_mine_block_hash_is_deterministic_for_nonce():
    block = Block(index=1, data="abc", previous_hash="0" * 64, difficulty=2)
    mine_block(block)
    winning_nonce = block.nonce
    winning_hash = block.hash_hex()
    # Recomputing with the same nonce yields the same hash.
    block.nonce = winning_nonce
    assert block.hash_hex() == winning_hash


def test_mine_block_gives_up_at_max_nonce():
    block = Block(index=1, data="x", previous_hash="0" * 64, difficulty=8)
    with pytest.raises(RuntimeError):
        mine_block(block, max_nonce=50)


def test_chain_builds_and_validates():
    chain = Blockchain(difficulty=3)
    chain.add_block("first")
    chain.add_block("second")
    assert len(chain.blocks) == 3  # genesis + 2
    assert chain.blocks[0].data == "genesis"
    assert chain.blocks[0].previous_hash == "0" * 64
    assert chain.is_valid()
    # every block links to its predecessor
    for i in range(1, len(chain.blocks)):
        assert chain.blocks[i].previous_hash == chain.blocks[i - 1].hash_hex()


def test_tampering_breaks_chain():
    chain = Blockchain(difficulty=3)
    chain.add_block("payload")
    assert chain.is_valid()
    # Mutating data invalidates that block's proof-of-work.
    chain.blocks[1].data = "tampered"
    assert not chain.is_valid()
