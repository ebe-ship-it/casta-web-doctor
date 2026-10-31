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
    response = app.test_client().post("/api/scan", json={"url": "ftp://example.com", "authorized": True})
    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_api_rejects_private_destination():
    response = app.test_client().post("/api/scan", json={"url": "http://127.0.0.1", "authorized": True})
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

    response = app.test_client().post("/api/scan", json={"url": "example.com", "authorized": True})

    assert response.status_code == 200
    assert response.get_json()["ok"] is True
    assert response.get_json()["response_time_ms"] == 42
    assert response.headers["Cache-Control"] == "no-store"



def test_api_returns_service_unavailable_when_hosted_scanning_is_unprotected(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.delenv("SSRF_EGRESS_PROTECTED", raising=False)

    response = app.test_client().post("/api/scan", json={"url": "example.com", "authorized": True})

    assert response.status_code == 503
    assert response.get_json()["ok"] is False
    assert response.get_json()["error"]["code"] == "security_configuration"



def test_stream_endpoint_delivers_real_progress_and_report(monkeypatch):
    fake_report = {
        "scan_type": "live",
        "ok": True,
        "url": "https://example.com",
        "status_code": 200,
        "response_time_ms": 15,
        "final_url": "https://example.com/",
        "uses_https": True,
        "redirect_count": 0,
        "security_headers": [],
        "error": None,
    }

    def fake_scan(url, on_progress=None):
        on_progress({"stage": "started", "message": "Scan request accepted"})
        on_progress({"stage": "request_started", "message": "Waiting for response headers"})
        on_progress({"stage": "completed", "message": "Scan completed", "status_code": 200})
        return fake_report

    monkeypatch.setattr(webapp, "scan_website", fake_scan)
    response = app.test_client().post(
        "/api/scan/stream",
        json={"url": "example.com", "authorized": True},
        buffered=True,
    )

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    assert '"stage":"started"' in body
    assert '"stage":"request_started"' in body
    assert '"type":"result"' in body
    assert '"status_code":200' in body
    assert response.headers["Cache-Control"] == "no-cache, no-store"


def test_stream_endpoint_rejects_non_object_json():
    response = app.test_client().post("/api/scan/stream", json=["example.com"])
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_request"


def test_api_requires_authorization_acknowledgement():
    response = app.test_client().post("/api/scan", json={"url": "example.com"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "authorization_required"


def test_stream_requires_authorization_acknowledgement():
    response = app.test_client().post("/api/scan/stream", json={"url": "example.com"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "authorization_required"



@pytest.mark.parametrize("acknowledgement", [False, None, 0, 1, "true", "yes", {}])
@pytest.mark.parametrize("endpoint", ["/api/scan", "/api/scan/stream"])
def test_scan_endpoints_reject_non_boolean_permission_acknowledgement(
    monkeypatch, endpoint, acknowledgement
):
    def unexpected_scan(*args, **kwargs):
        raise AssertionError("Scanner must not run without an explicit boolean acknowledgment")

    monkeypatch.setattr(webapp, "scan_website", unexpected_scan)
    response = app.test_client().post(
        endpoint,
        json={"url": "example.com", "authorized": acknowledgement},
        buffered=True,
    )

    assert response.status_code == 400
    assert response.get_json()["ok"] is False
    assert response.get_json()["error"]["code"] == "authorization_required"
