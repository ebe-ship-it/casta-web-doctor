import pytest

import webapp
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


@pytest.mark.parametrize("payload", [
    [],
    ["example.com"],
    "example.com",
    42,
    True,
])
def test_api_rejects_json_that_is_not_an_object(payload):
    response = app.test_client().post("/api/scan", json=payload)

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert response.get_json()["error"]["code"] == "invalid_request"


def test_api_rejects_json_null():
    response = app.test_client().post(
        "/api/scan",
        data="null",
        content_type="application/json",
    )

    assert response.status_code == 400
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


def test_api_returns_successful_scan(monkeypatch):
    fake_report = {
        "scan_type": "live",
        "ok": True,
        "url": "https://example.com",
        "status_code": 200,
        "response_time_ms": 42,
        "final_url": "https://example.com/",
        "uses_https": True,
        "redirect_count": 0,
        "security_headers": [],
        "error": None,
    }
    monkeypatch.setattr(webapp, "scan_website", lambda url: fake_report)

    response = app.test_client().post("/api/scan", json={"url": "example.com"})

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert response.get_json()["response_time_ms"] == 42
    assert response.headers["Cache-Control"] == "no-store"



def test_privacy_notice_is_published():
    response = app.test_client().get("/privacy")
    assert response.status_code == 200
    assert b"Privacy notice" in response.data
    assert b"retention period" in response.data


def test_acceptable_use_policy_is_published():
    response = app.test_client().get("/acceptable-use")
    assert response.status_code == 200
    assert b"Acceptable use policy" in response.data
    assert b"permission" in response.data.lower()


def test_homepage_links_to_policies():
    response = app.test_client().get("/")
    assert b'href="/privacy"' in response.data
    assert b'href="/acceptable-use"' in response.data
