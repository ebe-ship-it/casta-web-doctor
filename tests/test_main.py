import requests
import scanner

from main import check_website


class FakeResponse:
    def __init__(self, url="https://example.com/", status_code=200):
        self.url = url
        self.status_code = status_code
        self.headers = {
            "Strict-Transport-Security": "max-age=31536000",
            "Content-Security-Policy": "default-src 'self'",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
        }


def test_adds_https_to_domain(monkeypatch, capsys):
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return FakeResponse()

    monkeypatch.setattr(scanner._http_session, "get", fake_get)

    check_website("example.com")

    assert calls == ["https://example.com"]
    assert "Status code: 200" in capsys.readouterr().out


def test_reports_http_status(monkeypatch, capsys):
    def fake_get(url, **kwargs):
        return FakeResponse(status_code=404)

    monkeypatch.setattr(scanner._http_session, "get", fake_get)

    check_website("https://example.com")

    output = capsys.readouterr().out
    assert "Status code: 404" in output


def test_reports_missing_security_headers(monkeypatch, capsys):
    def fake_get(url, **kwargs):
        response = FakeResponse()
        response.headers = {}
        return response

    monkeypatch.setattr(scanner._http_session, "get", fake_get)

    check_website("https://example.com")

    output = capsys.readouterr().out
    assert "Content-Security-Policy not detected" in output


def test_handles_timeout(monkeypatch, capsys):
    def fake_get(url, **kwargs):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(scanner._http_session, "get", fake_get)

    check_website("https://example.com")

    output = capsys.readouterr().out
    assert "too long to respond" in output


def test_rejects_invalid_url(capsys):
    check_website("https:///")

    output = capsys.readouterr().out
    assert "Invalid website address" in output
