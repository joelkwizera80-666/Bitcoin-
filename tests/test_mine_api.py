import pytest

from bitcoin_app.app import create_app, MAX_WEB_DIFFICULTY


@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as c:
        yield c


def test_mine_endpoint_ok(client):
    resp = client.post("/api/mine", json={"data": "hello", "difficulty": 3})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["difficulty"] == 3
    assert body["target_prefix"] == "000"
    assert body["hash"].startswith("000")
    assert body["hashes"] == body["nonce"] + 1
    assert body["hashrate"] >= 0


def test_mine_endpoint_rejects_high_difficulty(client):
    resp = client.post("/api/mine", json={"difficulty": MAX_WEB_DIFFICULTY + 1})
    assert resp.status_code == 400


def test_mine_endpoint_rejects_non_integer(client):
    resp = client.post("/api/mine", json={"difficulty": "abc"})
    assert resp.status_code == 400
