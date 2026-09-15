"""CLI — toolkit + 666 Intelligence."""

from __future__ import annotations

import argparse
import json
import sys

from . import (
    btc_to_satoshi,
    satoshi_to_btc,
    generate_keypair,
    is_valid_address,
)
from .intelligence import chart_fees, plot_route, recon_address
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


def _cmd_fees(_args: argparse.Namespace) -> int:
    fees = chart_fees()
    tag = "live" if fees.live else "offline"
    print(f"fee chart ({fees.source}, {tag}) sats/vB")
    print(f"  fastest    {fees.fastest}")
    print(f"  half-hour  {fees.half_hour}")
    print(f"  hour       {fees.hour}")
    print(f"  economy    {fees.economy}")
    print(f"  minimum    {fees.minimum}")
    return 0


def _cmd_recon(args: argparse.Namespace) -> int:
    d = recon_address(args.address)
    print(json.dumps(d.as_dict(), indent=2))
    return 0 if d.valid else 1


def _cmd_route(args: argparse.Namespace) -> int:
    try:
        route = plot_route(args.destination, args.sats, args.vbytes)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(route, indent=2))
    return 0 if route["clearance"] == "GO" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bitcoin-app",
        description="Bitcoin toolkit + 666 Intelligence (ROBIN BANKS / CAPTAINCOOKCRYPTO)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_conv = sub.add_parser("convert", help="convert between BTC and satoshis")
    p_conv.add_argument("--btc", type=str, default=None)
    p_conv.add_argument("--sats", type=int, default=None)
    p_conv.set_defaults(func=_cmd_convert)

    p_val = sub.add_parser("validate", help="validate a Base58Check address")
    p_val.add_argument("address")
    p_val.set_defaults(func=_cmd_validate)

    p_key = sub.add_parser("keygen", help="generate a new keypair + address")
    p_key.set_defaults(func=_cmd_keygen)

    p_price = sub.add_parser("price", help="fetch the live BTC price")
    p_price.add_argument("--currency", default="usd")
    p_price.set_defaults(func=_cmd_price)

    p_fees = sub.add_parser("fees", help="666 Intel fee chart")
    p_fees.set_defaults(func=_cmd_fees)

    p_recon = sub.add_parser("recon", help="watch-only address dossier")
    p_recon.add_argument("address")
    p_recon.set_defaults(func=_cmd_recon)

    p_route = sub.add_parser("route", help="Captain Cook haul quote")
    p_route.add_argument("destination")
    p_route.add_argument("--sats", type=int, required=True)
    p_route.add_argument("--vbytes", type=int, default=140)
    p_route.set_defaults(func=_cmd_route)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
