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
)
from .prices import get_btc_price


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
