import socket
import ipaddress

import pytest
import requests
import scanner

from scanner import InvalidURLError, normalize_url, scan_website


class FakeResponse:
    def __init__(self, url="https://example.com/", status_code=200, headers=None):
        self.url = url
        self.status_code = status_code
        self.headers = headers if headers is not None else {}
        self.closed = False

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def stub_public_dns(monkeypatch):
    """Keep tests deterministic and independent of external DNS availability."""
    def fake_getaddrinfo(host, port, type=socket.SOCK_STREAM):
        return [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("93.184.216.34", port),
            )
        ]

    monkeypatch.setattr(scanner.socket, "getaddrinfo", fake_getaddrinfo)


def test_normalize_adds_https():
    assert normalize_url("example.com") == "https://example.com"


def test_normalize_keeps_http():
    assert normalize_url("http://example.com") == "http://example.com"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "   ",
        None,
        "https:///",
        "ftp://example.com",
        "exa mple.com",
        "example.com:abc",
        "https://example.com:80",
        "http://example.com:443",
        "https://user:password@example.com",
    ],
)
def test_normalize_rejects_bad_input(bad):
    with pytest.raises(InvalidURLError):
        normalize_url(bad)


def test_normalize_removes_fragment():
    assert normalize_url("https://example.com/path#section") == "https://example.com/path"


def test_scan_success(monkeypatch):
    monkeypatch.setattr(scanner._http_session, "get", lambda url, **kw: FakeResponse())
    result = scan_website("example.com")
    assert result["ok"] is True
    assert result["status_code"] == 200
    assert result["uses_https"] is True
    assert len(result["security_headers"]) == 5


def test_scan_reports_final_url(monkeypatch):
    monkeypatch.setattr(
        requests,
        "get",
        lambda url, **kw: FakeResponse(url="https://www.example.com/home"),
    )
    result = scan_website("http://example.com")
    assert result["final_url"] == "https://www.example.com/home"


def test_scan_follows_safe_redirect_and_closes_responses(monkeypatch):
    responses = [
        FakeResponse(
            url="http://example.com/",
            status_code=301,
            headers={"Location": "https://example.com/home"},
        ),
        FakeResponse(url="https://example.com/home", status_code=200),
    ]
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return responses[len(calls) - 1]

    monkeypatch.setattr(scanner._http_session, "get", fake_get)
    result = scan_website("http://example.com")

    assert result["ok"] is True
    assert result["redirect_count"] == 1
    assert calls == ["http://example.com", "https://example.com/home"]
    assert responses[0].closed is True
    assert responses[1].closed is True


def test_scan_rejects_unsafe_redirect(monkeypatch):
    response = FakeResponse(
        url="http://example.com/",
        status_code=302,
        headers={"Location": "http://127.0.0.1/admin"},
    )
    monkeypatch.setattr(scanner._http_session, "get", lambda url, **kw: response)

    result = scan_website("http://example.com")

    assert result["ok"] is False
    assert result["error"]["code"] == "unsafe_redirect"
    assert response.closed is True


def test_scan_handles_timeout(monkeypatch):
    def fake_get(url, **kw):
        raise requests.exceptions.Timeout()

    monkeypatch.setattr(scanner._http_session, "get", fake_get)
    result = scan_website("example.com")
    assert result["ok"] is False
    assert result["error"]["code"] == "timeout"


def test_scan_reports_dns_failure_separately_from_invalid_url(monkeypatch):
    def fail_dns(host, port, type=socket.SOCK_STREAM):
        raise socket.gaierror("temporary resolver failure")

    monkeypatch.setattr(scanner.socket, "getaddrinfo", fail_dns)

    result = scan_website("valid-looking-domain.example")

    assert result["ok"] is False
    assert result["error"]["code"] == "dns_failed"


def test_invalid_url_does_not_make_request(monkeypatch):
    def fake_get(url, **kw):
        raise AssertionError("Request should not happen")

    monkeypatch.setattr(scanner._http_session, "get", fake_get)
    result = scan_website("https:///")
    assert result["error"]["code"] == "invalid_url"



def test_scan_rejects_redirect_without_location(monkeypatch):
    response = FakeResponse(
        url="https://example.com/",
        status_code=302,
        headers={},
    )
    monkeypatch.setattr(scanner._http_session, "get", lambda url, **kw: response)

    result = scan_website("example.com")

    assert result["ok"] is False
    assert result["error"]["code"] == "redirect_error"
    assert response.closed is True


def test_scan_stops_after_redirect_limit(monkeypatch):
    responses = [
        FakeResponse(
            url=f"https://example.com/{index}",
            status_code=302,
            headers={"Location": f"https://example.com/{index + 1}"},
        )
        for index in range(6)
    ]
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return responses[len(calls) - 1]

    monkeypatch.setattr(scanner._http_session, "get", fake_get)

    result = scan_website("example.com")

    assert result["ok"] is False
    assert result["error"]["code"] == "too_many_redirects"
    assert len(calls) == 6
    assert all(response.closed for response in responses)


def test_scan_uses_bounded_connect_and_read_timeouts(monkeypatch):
    captured = {}

    def fake_get(url, **kwargs):
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr(scanner._http_session, "get", fake_get)

    result = scan_website("example.com")

    assert result["ok"] is True
    connect_timeout, read_timeout = captured["timeout"]
    assert 0 < connect_timeout <= 8
    assert 0 < read_timeout <= 8



def test_dns_pinning_adapter_keeps_hostname_but_pins_ip(monkeypatch):
    adapter = scanner._DNSPinningAdapter()
    monkeypatch.setattr(
        scanner, "_resolve_public_addresses",
        lambda url: (scanner.urlparse(url), [ipaddress.ip_address("93.184.216.34")]),
    )
    pool = adapter.get_connection("https://example.com/path")
    assert pool.host == "example.com"
    assert pool.port == 443
    assert pool.conn_kw["pinned_ip"] == "93.184.216.34"


def test_dns_pinning_rejects_proxy_routing():
    adapter = scanner._DNSPinningAdapter()
    with pytest.raises(InvalidURLError, match="Proxy routing"):
        adapter.get_connection("https://example.com", proxies={"https": "http://proxy.invalid"})


def test_dns_resolution_rejects_mixed_public_and_private_answers(monkeypatch):
    def mixed_dns(host, port, type=socket.SOCK_STREAM):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port)),
            (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", port)),
        ]
    monkeypatch.setattr(scanner.socket, "getaddrinfo", mixed_dns)
    with pytest.raises(InvalidURLError, match="Private or non-public"):
        scanner._resolve_public_addresses("https://example.com")
