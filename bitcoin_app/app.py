"""Small Flask dashboard for the Bitcoin toolkit.

Run locally with::

    flask --app bitcoin_app.app run --host 0.0.0.0 --port 5000

or::

    python -m bitcoin_app.app
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from flask import Flask, jsonify, render_template, request

from . import (
    btc_to_satoshi,
    satoshi_to_btc,
    generate_keypair,
    is_valid_address,
    Block,
    mine_block,
)
from .prices import get_btc_price

# Cap difficulty so a single HTTP request stays responsive.
MAX_WEB_DIFFICULTY = 6


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        quote = get_btc_price("usd")
        return render_template("index.html", quote=quote)

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.get("/api/price")
    def api_price():
        currency = request.args.get("currency", "usd")
        quote = get_btc_price(currency)
        return jsonify(
            currency=quote.currency,
            price=quote.price,
            source=quote.source,
            live=quote.live,
        )

    @app.get("/api/convert")
    def api_convert():
        btc = request.args.get("btc")
        sats = request.args.get("sats")
        if (btc is None) == (sats is None):
            return jsonify(error="pass exactly one of btc or sats"), 400
        try:
            if btc is not None:
                value = btc_to_satoshi(btc)
                return jsonify(btc=btc, satoshis=value)
            value = str(satoshi_to_btc(int(sats)))
            return jsonify(satoshis=int(sats), btc=value)
        except (InvalidOperation, ValueError):
            return jsonify(error="invalid amount"), 400

    @app.get("/api/validate")
    def api_validate():
        address = request.args.get("address", "")
        return jsonify(address=address, valid=is_valid_address(address))

    @app.post("/api/mine")
    def api_mine():
        payload = request.get_json(silent=True) or {}
        data = str(payload.get("data", request.args.get("data", "hello block")))
        raw_difficulty = payload.get("difficulty", request.args.get("difficulty", 4))
        try:
            difficulty = int(raw_difficulty)
        except (TypeError, ValueError):
            return jsonify(error="difficulty must be an integer"), 400
        if not 1 <= difficulty <= MAX_WEB_DIFFICULTY:
            return jsonify(error=f"difficulty must be 1..{MAX_WEB_DIFFICULTY}"), 400

        block = Block(index=1, data=data, previous_hash="0" * 64, difficulty=difficulty)
        result = mine_block(block)
        return jsonify(
            data=data,
            difficulty=difficulty,
            target_prefix="0" * difficulty,
            hash=result.hash_hex,
            nonce=result.nonce,
            hashes=result.hashes,
            elapsed_s=round(result.elapsed_s, 4),
            hashrate=round(result.hashrate, 1),
        )

    @app.post("/api/keygen")
    def api_keygen():
        kp = generate_keypair()
        return jsonify(
            private_key_hex=kp.private_key_hex,
            wif=kp.wif,
            public_key_hex=kp.public_key_hex,
            address=kp.address,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
