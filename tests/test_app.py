import pytest

from bitcoin_app.app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_index_renders(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Bitcoin- Toolkit" in resp.data


def test_convert_btc(client):
    resp = client.get("/api/convert?btc=0.5")
    assert resp.status_code == 200
    assert resp.get_json()["satoshis"] == 50_000_000


def test_convert_requires_one_arg(client):
    assert client.get("/api/convert").status_code == 400
    assert client.get("/api/convert?btc=1&sats=1").status_code == 400


def test_validate_endpoint(client):
    good = client.get("/api/validate?address=1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    assert good.get_json()["valid"] is True
    bad = client.get("/api/validate?address=nope")
    assert bad.get_json()["valid"] is False


def test_keygen_endpoint(client):
    resp = client.post("/api/keygen")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(body) == {"private_key_hex", "wif", "public_key_hex", "address"}
    assert body["address"].startswith("1")
