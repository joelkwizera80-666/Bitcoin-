from decimal import Decimal

import pytest

from bitcoin_app import (
    SATOSHIS_PER_BTC,
    btc_to_satoshi,
    satoshi_to_btc,
    b58check_encode,
    b58check_decode,
    is_valid_address,
    generate_keypair,
    pubkey_to_p2pkh_address,
)


def test_btc_to_satoshi_whole():
    assert btc_to_satoshi(1) == SATOSHIS_PER_BTC
    assert btc_to_satoshi("0.5") == 50_000_000
    assert btc_to_satoshi("0.00000001") == 1


def test_satoshi_to_btc_roundtrip():
    assert satoshi_to_btc(SATOSHIS_PER_BTC) == Decimal("1.00000000")
    assert satoshi_to_btc(1) == Decimal("0.00000001")
    for sats in (0, 1, 12345678, 100_000_000, 2_100_000_000_000_000):
        assert btc_to_satoshi(satoshi_to_btc(sats)) == sats


def test_b58check_roundtrip():
    payload = bytes([0x00]) + b"\x11" * 20
    encoded = b58check_encode(payload)
    assert b58check_decode(encoded) == payload


def test_b58check_bad_checksum():
    payload = bytes([0x00]) + b"\x11" * 20
    encoded = b58check_encode(payload)
    tampered = encoded[:-1] + ("A" if encoded[-1] != "A" else "B")
    with pytest.raises(ValueError):
        b58check_decode(tampered)


@pytest.mark.parametrize(
    "address",
    [
        "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",  # Satoshi genesis coinbase address
        "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
    ],
)
def test_known_addresses_valid(address):
    assert is_valid_address(address)


@pytest.mark.parametrize(
    "address",
    [
        "",
        "not-an-address",
        "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN3",  # last char tweaked -> bad checksum
        "0OIl",  # invalid base58 characters
    ],
)
def test_invalid_addresses(address):
    assert not is_valid_address(address)


def test_generate_keypair_is_valid():
    kp = generate_keypair()
    assert is_valid_address(kp.address)
    assert kp.address.startswith("1")
    assert len(bytes.fromhex(kp.private_key_hex)) == 32
    # compressed pubkey: 33 bytes, prefix 02 or 03
    pub = bytes.fromhex(kp.public_key_hex)
    assert len(pub) == 33 and pub[0] in (2, 3)
    # address must be derivable from the reported pubkey
    assert pubkey_to_p2pkh_address(pub) == kp.address


def test_generated_keypairs_are_unique():
    addrs = {generate_keypair().address for _ in range(5)}
    assert len(addrs) == 5
