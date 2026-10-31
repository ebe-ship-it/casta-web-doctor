from webapp import app


def test_homepage_loads():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Casta" in response.data
    assert b"Scan website" in response.data


def test_health_endpoint():
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_api_rejects_non_json():
    response = app.test_client().post("/api/scan", data="example.com")
    assert response.status_code == 415


def test_api_rejects_invalid_url():
    response = app.test_client().post("/api/scan", json={"url": "ftp://example.com"})
    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_api_rejects_private_destination():
    response = app.test_client().post("/api/scan", json={"url": "http://127.0.0.1"})
    assert response.status_code == 400
    assert response.get_json()["ok"] is False
