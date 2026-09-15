from bitcoin_app.intelligence import classify_vault, plot_route, recon_address


def test_classify_fog():
    label, notes = classify_vault(0, 0, False)
    assert label == "FOG"
    assert notes


def test_classify_dark():
    label, _ = classify_vault(0, 0, True)
    assert label == "DARK"


def test_classify_spent():
    label, _ = classify_vault(0, 3, True)
    assert label == "SPENT"


def test_classify_hold():
    label, _ = classify_vault(100_000_000, 2, True)
    assert label == "HOLD"


def test_recon_invalid_offline():
    d = recon_address("not-an-address", allow_network=False)
    assert d.valid is False
    assert d.classification == "FOG"
    assert d.live is False


def test_recon_valid_offline():
    d = recon_address("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", allow_network=False)
    assert d.valid is True
    assert d.classification == "DARK"
    assert d.live is False


def test_plot_route_offline_hold_on_zero():
    route = plot_route("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 0, allow_network=False)
    assert route["clearance"] == "HOLD"
    assert route["chain"] == "bitcoin-l1"
    assert route["product"] == "ROBIN BANKS"


def test_plot_route_offline_go():
    route = plot_route("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", 50_000, vbytes=140, allow_network=False)
    assert route["clearance"] == "GO"
    assert route["fee_sats"] == 20 * 140
    assert route["total_sats"] == 50_000 + 2800
