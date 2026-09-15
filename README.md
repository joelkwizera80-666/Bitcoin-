# Bitcoin-

A small, dependency-light **Bitcoin toolkit** written in Python. It ships a
reusable library, a command-line interface, and a tiny Flask web dashboard so
the project is runnable end to end.

## Features

- BTC &harr; satoshi conversion (exact, `Decimal`-based)
- Base58Check encode/decode with checksum verification
- Mainnet P2PKH address validation
- secp256k1 keypair + address generation (private key, WIF, compressed pubkey)
- Live BTC price via the public CoinGecko API (graceful offline fallback)
- SHA-256 proof-of-work miner + minimal blockchain (double-SHA-256, difficulty
  target, chain validation)

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

### Command line

```bash
python -m bitcoin_app.cli convert --btc 0.5
python -m bitcoin_app.cli convert --sats 150000000
python -m bitcoin_app.cli validate 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
python -m bitcoin_app.cli keygen
python -m bitcoin_app.cli price --currency usd
python -m bitcoin_app.cli mine --difficulty 4 --blocks 3
```

### Web dashboard

```bash
flask --app bitcoin_app.app run --host 0.0.0.0 --port 5000
# then open http://localhost:5000
```

### Tests

```bash
python -m pytest
```

## Cloud Agent environment

This repo is configured for Cursor Cloud Agents via
[`.cursor/environment.json`](.cursor/environment.json):

- **install** — `bash .cursor/install.sh` creates a virtualenv and installs
  `requirements.txt` (installing `python3-venv` first if needed). It is
  idempotent.
- **terminals** — a `web` terminal runs the Flask dev server on port `5000`.

## Disclaimer

This is an educational toolkit. Do not use generated keys to custody real funds.
