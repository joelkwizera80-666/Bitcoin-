"""Flask dashboard + 666 Intelligence API."""

from __future__ import annotations

from decimal import InvalidOperation

from flask import Flask, jsonify, render_template, request

from . import (
    btc_to_satoshi,
    satoshi_to_btc,
    generate_keypair,
    is_valid_address,
)
from .intelligence import chart_fees, plot_route, recon_address
from .prices import get_btc_price


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        quote = get_btc_price("usd")
        fees = chart_fees()
        return render_template("index.html", quote=quote, fees=fees)

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok", unit="CAPTAINCOOKCRYPTO", product="ROBIN BANKS")

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

    @app.post("/api/keygen")
    def api_keygen():
        kp = generate_keypair()
        return jsonify(
            private_key_hex=kp.private_key_hex,
            wif=kp.wif,
            public_key_hex=kp.public_key_hex,
            address=kp.address,
        )

    @app.get("/api/intel/fees")
    def api_fees():
        return jsonify(chart_fees().as_dict())

    @app.get("/api/intel/recon")
    def api_recon():
        address = request.args.get("address", "")
        if not address:
            return jsonify(error="address required"), 400
        return jsonify(recon_address(address).as_dict())

    @app.get("/api/intel/route")
    def api_route():
        destination = request.args.get("destination", "")
        try:
            sats = int(request.args.get("sats", "0"))
            vbytes = int(request.args.get("vbytes", "140"))
        except ValueError:
            return jsonify(error="sats and vbytes must be integers"), 400
        if not destination:
            return jsonify(error="destination required"), 400
        try:
            return jsonify(plot_route(destination, sats, vbytes))
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
