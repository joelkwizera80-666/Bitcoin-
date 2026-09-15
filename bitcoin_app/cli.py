"""Command-line interface for the Bitcoin toolkit.

Examples::

    python -m bitcoin_app.cli convert --btc 0.5
    python -m bitcoin_app.cli convert --sats 150000000
    python -m bitcoin_app.cli validate 1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2
    python -m bitcoin_app.cli keygen
    python -m bitcoin_app.cli price --currency usd
"""

from __future__ import annotations

import argparse
import sys

from . import (
    btc_to_satoshi,
    satoshi_to_btc,
    generate_keypair,
    is_valid_address,
    Blockchain,
    BlockHeader,
    mine_header,
    compute_merkle_root,
    txid_from_raw,
    target_from_leading_zero_bits,
    target_to_bits,
    bits_to_target,
)
from .prices import get_btc_price

# Bitcoin genesis block, for verifying the real Proof-of-Work implementation.
GENESIS = {
    "version": 1,
    "prev_hash_hex": "0" * 64,
    "merkle_root_hex": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
    "timestamp": 1231006505,
    "bits": 0x1D00FFFF,
    "nonce": 2083236893,
    "hash_hex": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
}
GENESIS_COINBASE_RAW = (
    "01000000010000000000000000000000000000000000000000000000000000000000000000"
    "ffffffff4d04ffff001d0104455468652054696d65732030332f4a616e2f3230303920436861"
    "6e63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f757420666f72"
    "2062616e6b73ffffffff0100f2052a01000000434104678afdb0fe5548271967f1a67130b710"
    "5cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0b"
    "8d578a4c702b6bf11d5fac00000000"
)


def _cmd_convert(args: argparse.Namespace) -> int:
    if (args.btc is None) == (args.sats is None):
        print("error: pass exactly one of --btc or --sats", file=sys.stderr)
        return 2
    if args.btc is not None:
        sats = btc_to_satoshi(args.btc)
        print(f"{args.btc} BTC = {sats:,} satoshis")
    else:
        btc = satoshi_to_btc(args.sats)
        print(f"{args.sats:,} satoshis = {btc} BTC")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    ok = is_valid_address(args.address)
    print(f"{args.address}: {'VALID' if ok else 'INVALID'}")
    return 0 if ok else 1


def _cmd_keygen(_args: argparse.Namespace) -> int:
    kp = generate_keypair()
    print(f"private_key_hex : {kp.private_key_hex}")
    print(f"wif             : {kp.wif}")
    print(f"public_key_hex  : {kp.public_key_hex}")
    print(f"address         : {kp.address}")
    return 0


def _cmd_mine(args: argparse.Namespace) -> int:
    chain = Blockchain(difficulty=args.difficulty)
    print(f"Mining {args.blocks} block(s) at difficulty {args.difficulty} "
          f"(target prefix '{'0' * args.difficulty}')\n")
    for n in range(1, args.blocks + 1):
        result = chain.add_block(f"{args.data} #{n}")
        rate = result.hashrate
        print(
            f"block {result.block.index}: hash={result.hash_hex} "
            f"nonce={result.nonce:,} hashes={result.hashes:,} "
            f"time={result.elapsed_s:.3f}s rate={rate:,.0f} H/s"
        )
    print(f"\nchain valid: {chain.is_valid()}  length: {len(chain.blocks)} blocks")
    return 0


def _cmd_pow(args: argparse.Namespace) -> int:
    if args.verify_genesis:
        return _verify_genesis()

    txid = txid_from_raw(args.data.encode("utf-8"))
    merkle_root = compute_merkle_root([txid])
    target = target_from_leading_zero_bits(args.zero_bits)
    bits = target_to_bits(target)
    header = BlockHeader(
        version=args.version,
        prev_hash=bytes.fromhex(args.prev)[::-1],
        merkle_root=merkle_root,
        bits=bits,
    )
    print(
        f"Mining real-style header: bits={bits:#010x} "
        f"(~{args.zero_bits} leading zero bits), difficulty={header.difficulty():.8f}\n"
    )
    result = mine_header(header)
    print(f"block hash : {result.hash_hex}")
    print(f"nonce      : {result.nonce:,}")
    print(f"hashes     : {result.hashes:,}")
    print(f"time       : {result.elapsed_s:.3f}s")
    print(f"rate       : {result.hashrate:,.0f} H/s")
    print(f"valid PoW  : {header.is_valid_pow()}")
    return 0


def _verify_genesis() -> int:
    merkle = compute_merkle_root([txid_from_raw(bytes.fromhex(GENESIS_COINBASE_RAW))])
    merkle_hex = merkle[::-1].hex()
    header = BlockHeader.from_hex(
        version=GENESIS["version"],
        prev_hash_hex=GENESIS["prev_hash_hex"],
        merkle_root_hex=GENESIS["merkle_root_hex"],
        bits=GENESIS["bits"],
        timestamp=GENESIS["timestamp"],
        nonce=GENESIS["nonce"],
    )
    computed = header.hash_hex()
    merkle_ok = merkle_hex == GENESIS["merkle_root_hex"]
    hash_ok = computed == GENESIS["hash_hex"]
    pow_ok = header.is_valid_pow()

    print("Bitcoin genesis block verification")
    print(f"  merkle root (from coinbase): {merkle_hex}")
    print(f"    expected                 : {GENESIS['merkle_root_hex']}  -> {'OK' if merkle_ok else 'MISMATCH'}")
    print(f"  block hash (from header)   : {computed}")
    print(f"    expected                 : {GENESIS['hash_hex']}  -> {'OK' if hash_ok else 'MISMATCH'}")
    print(f"  difficulty                 : {header.difficulty():.8f}")
    print(f"  hash <= target (valid PoW) : {pow_ok}")
    return 0 if (merkle_ok and hash_ok and pow_ok) else 1


def _cmd_price(args: argparse.Namespace) -> int:
    quote = get_btc_price(args.currency)
    if quote.live:
        print(f"1 BTC = {quote.price:,.2f} {quote.currency.upper()} (via {quote.source})")
        return 0
    print("price unavailable (offline)", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bitcoin-app", description="Bitcoin toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    p_conv = sub.add_parser("convert", help="convert between BTC and satoshis")
    p_conv.add_argument("--btc", type=str, default=None, help="amount in BTC")
    p_conv.add_argument("--sats", type=int, default=None, help="amount in satoshis")
    p_conv.set_defaults(func=_cmd_convert)

    p_val = sub.add_parser("validate", help="validate a Base58Check address")
    p_val.add_argument("address")
    p_val.set_defaults(func=_cmd_validate)

    p_key = sub.add_parser("keygen", help="generate a new keypair + address")
    p_key.set_defaults(func=_cmd_keygen)

    p_mine = sub.add_parser("mine", help="mine blocks with SHA-256 proof-of-work")
    p_mine.add_argument("--difficulty", type=int, default=4,
                        help="required leading zero hex digits (default 4)")
    p_mine.add_argument("--blocks", type=int, default=1, help="number of blocks to mine")
    p_mine.add_argument("--data", default="block", help="payload label for each block")
    p_mine.set_defaults(func=_cmd_mine)

    p_pow = sub.add_parser(
        "pow", help="Bitcoin-accurate proof-of-work (80-byte header, nBits target)"
    )
    p_pow.add_argument("--zero-bits", type=int, default=16,
                       help="approx leading zero bits in the target (default 16)")
    p_pow.add_argument("--data", default="hello block", help="single-tx payload")
    p_pow.add_argument("--version", type=int, default=1, help="block version")
    p_pow.add_argument("--prev", default="0" * 64, help="previous block hash (display hex)")
    p_pow.add_argument("--verify-genesis", action="store_true",
                       help="reproduce and verify Bitcoin's genesis block hash")
    p_pow.set_defaults(func=_cmd_pow)

    p_price = sub.add_parser("price", help="fetch the live BTC price")
    p_price.add_argument("--currency", default="usd")
    p_price.set_defaults(func=_cmd_price)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
