import pytest
import requests

from scanner import InvalidURLError, normalize_url, scan_website


class FakeResponse:
    def __init__(self, url="https://example.com/", status_code=200, headers=None):
        self.url = url
        self.status_code = status_code
        self.headers = headers if headers is not None else {}


def test_normalize_adds_https():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_keeps_http():
    assert normalize_url("http://example.com") == "http://example.com"


@pytest.mark.parametrize(
    "bad",
    ["", "   ", None, "https:///", "ftp://example.com",
     "exa mple.com", "example.com:abc"],
)
def test_normalize_rejects_bad_input(bad):
    with pytest.raises(InvalidURLError):
        normalize_url(bad)


def test_scan_success(monkeypatch):
    monkeypatch.setattr(
        requests, "get", lambda url, **kw: FakeResponse()
    )
    result = scan_website("example.com")
    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["uses_https"] is True


def test_scan_reports_final_url(monkeypatch):
    monkeypatch.setattr(
        requests, "get",
        lambda url, **kw: FakeResponse(url="https://www.example.com/home"),
    )
    result = scan_website("http://example.com")
    assert result["final_url"] == "https://www.example.com/home"


def test_scan_handles_timeout(monkeypatch):
    def fake_get(url, **kw):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(requests, "get", fake_get)
    result = scan_website("example.com")
    assert result["ok"] is False
    assert result["error"]["code"] == "timeout"


def test_invalid_url_does_not_make_request(monkeypatch):
    def fake_get(url, **kw):
        raise AssertionError("Request should not happen")

    monkeypatch.setattr(requests, "get", fake_get)
    result = scan_website("https:///")
    assert result["error"]["code"] == "invalid_url"
