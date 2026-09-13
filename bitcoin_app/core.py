"""Core Bitcoin primitives.

Everything here works offline and is deterministic (except key generation,
which draws from ``os.urandom`` via the ``ecdsa`` library). The functions cover
the pieces needed to demonstrate a working end-to-end flow: converting between
BTC and satoshis, Base58Check (de)coding, deriving a mainnet P2PKH address from
a public key, validating an address checksum, and generating a fresh keypair.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN

from ecdsa import SigningKey, SECP256k1

SATOSHIS_PER_BTC = 100_000_000

# Base58 alphabet used by Bitcoin (no 0, O, I, l).
_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_INDEX = {ch: i for i, ch in enumerate(_B58_ALPHABET)}

# Mainnet version bytes.
_P2PKH_VERSION = 0x00
_WIF_VERSION = 0x80


def btc_to_satoshi(btc) -> int:
    """Convert a BTC amount to an integer number of satoshis.

    Uses ``Decimal`` to avoid binary floating-point rounding surprises.
    """
    amount = Decimal(str(btc))
    sats = (amount * SATOSHIS_PER_BTC).quantize(Decimal(1), rounding=ROUND_DOWN)
    return int(sats)


def satoshi_to_btc(satoshi: int) -> Decimal:
    """Convert an integer number of satoshis to a BTC ``Decimal``."""
    return (Decimal(int(satoshi)) / SATOSHIS_PER_BTC).quantize(Decimal("0.00000001"))


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _double_sha256(data: bytes) -> bytes:
    return _sha256(_sha256(data))


def hash160(data: bytes) -> bytes:
    """RIPEMD160(SHA256(data)), the standard Bitcoin ``HASH160``."""
    ripemd = hashlib.new("ripemd160")
    ripemd.update(_sha256(data))
    return ripemd.digest()


def b58check_encode(payload: bytes) -> str:
    """Encode ``payload`` (version + data) with a 4-byte double-SHA256 checksum."""
    checksum = _double_sha256(payload)[:4]
    full = payload + checksum

    # Count leading zero bytes; each becomes a leading '1'.
    n_pad = len(full) - len(full.lstrip(b"\x00"))

    num = int.from_bytes(full, "big")
    encoded = ""
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = _B58_ALPHABET[rem] + encoded

    return "1" * n_pad + encoded


def b58check_decode(text: str) -> bytes:
    """Decode a Base58Check string, verifying and stripping the checksum.

    Returns the ``payload`` (version byte + data). Raises ``ValueError`` on an
    invalid character or a bad checksum.
    """
    n_pad = len(text) - len(text.lstrip("1"))

    num = 0
    for ch in text:
        if ch not in _B58_INDEX:
            raise ValueError(f"invalid base58 character: {ch!r}")
        num = num * 58 + _B58_INDEX[ch]

    body = num.to_bytes((num.bit_length() + 7) // 8, "big") if num else b""
    full = b"\x00" * n_pad + body

    if len(full) < 4:
        raise ValueError("string too short to contain a checksum")

    payload, checksum = full[:-4], full[-4:]
    if _double_sha256(payload)[:4] != checksum:
        raise ValueError("bad checksum")
    return payload


def pubkey_to_p2pkh_address(pubkey: bytes, version: int = _P2PKH_VERSION) -> str:
    """Derive a mainnet P2PKH address from a raw public key."""
    payload = bytes([version]) + hash160(pubkey)
    return b58check_encode(payload)


def is_valid_address(address: str) -> bool:
    """Return ``True`` if ``address`` is a well-formed Base58Check address."""
    try:
        payload = b58check_decode(address)
    except ValueError:
        return False
    # version byte + 20-byte HASH160.
    return len(payload) == 21


@dataclass
class KeyPair:
    """A freshly generated Bitcoin keypair and its derived address."""

    private_key_hex: str
    wif: str
    public_key_hex: str
    address: str


def _encode_wif(private_key: bytes, compressed: bool = True) -> str:
    payload = bytes([_WIF_VERSION]) + private_key + (b"\x01" if compressed else b"")
    return b58check_encode(payload)


def _compressed_pubkey(vk) -> bytes:
    point = vk.pubkey.point
    x = point.x().to_bytes(32, "big")
    prefix = b"\x02" if point.y() % 2 == 0 else b"\x03"
    return prefix + x


def generate_keypair() -> KeyPair:
    """Generate a random secp256k1 keypair with a compressed mainnet address."""
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()

    private_key = sk.to_string()
    pubkey = _compressed_pubkey(vk)

    return KeyPair(
        private_key_hex=private_key.hex(),
        wif=_encode_wif(private_key, compressed=True),
        public_key_hex=pubkey.hex(),
        address=pubkey_to_p2pkh_address(pubkey),
    )
