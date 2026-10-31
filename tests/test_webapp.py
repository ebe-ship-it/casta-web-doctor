from webapp import app


def test_homepage_loads():
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert b"Casta Web Doctor" in response.data
    assert b"Check website" in response.data
    assert b"Georgia" in response.data


def test_homepage_has_security_headers():
    response = app.test_client().get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_health_endpoint():
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
    assert response.headers["Cache-Control"] == "no-store"


def test_api_rejects_non_json():
    response = app.test_client().post("/api/scan", data="example.com")
    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "invalid_request"


def test_api_rejects_invalid_url():
    response = app.test_client().post("/api/scan", json={"url": "ftp://example.com"})
    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_api_rejects_private_destination():
    response = app.test_client().post("/api/scan", json={"url": "http://127.0.0.1"})
    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_api_rejects_oversized_request():
    response = app.test_client().post(
        "/api/scan",
        data='{"url":"' + ("a" * 9000) + '"}',
        content_type="application/json",
    )
    assert response.status_code == 413
    assert response.get_json()["error"]["code"] == "request_too_large"
