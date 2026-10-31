"""Casta Web Doctor's bounded website scanner.

Only public HTTP(S) destinations on their standard ports are allowed. Redirects
are validated individually and limited. Public deployments still need outbound
network controls to protect against DNS-rebinding races.
"""
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlparse, urlunparse

import requests

USER_AGENT = "CastaWebDoctor/1.1"
TIMEOUT_SECONDS = 8
MAX_URL_LENGTH = 2048
MAX_REDIRECTS = 5

SECURITY_HEADERS = {
    "Strict-Transport-Security": "Tells browsers to prefer HTTPS for this site.",
    "Content-Security-Policy": "Restricts where scripts and other content can load from.",
    "X-Content-Type-Options": "Helps prevent browsers from guessing file types; use nosniff.",
    "Referrer-Policy": "Controls how much page address information is shared with other sites.",
    "Permissions-Policy": "Controls access to browser features such as camera and microphone.",
}


class InvalidURLError(ValueError):
    """Raised when the website address cannot safely be scanned."""


def normalize_url(raw_url):
    """Return a normalized HTTP(S) URL, or raise InvalidURLError."""
    if not isinstance(raw_url, str):
        raise InvalidURLError("Enter a valid website address.")
    url = raw_url.strip()
    if not url or len(url) > MAX_URL_LENGTH or any(c.isspace() for c in url):
        raise InvalidURLError("Enter a valid website address.")
    if "://" not in url:
        url = "https://" + url

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise InvalidURLError("Enter a valid website address.") from exc

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise InvalidURLError("Only HTTP and HTTPS addresses are supported.")
    if not hostname or parsed.username is not None or parsed.password is not None:
        raise InvalidURLError(
            "Invalid website address: missing hostname or embedded credentials are not allowed."
        )

    # Do not allow scheme/port mismatches, alternate services, or non-standard ports.
    expected_port = 80 if scheme == "http" else 443
    if port is not None and port != expected_port:
        raise InvalidURLError(
            "For safety, use HTTP on port 80 or HTTPS on port 443."
        )

    # Fragments are browser-only and are not sent to the web server.
    return urlunparse(
        (scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, "")
    )


def _validate_public_destination(url):
    """Reject local, private, reserved, and non-public destinations."""
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    host = parsed.hostname.rstrip(".").lower()

    if (
        host == "localhost"
        or host.endswith(".localhost")
        or host.endswith(".local")
    ):
        raise InvalidURLError("Local and internal network addresses cannot be scanned.")

    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            records = socket.getaddrinfo(
                host,
                443 if parsed.scheme == "https" else 80,
                type=socket.SOCK_STREAM,
            )
        except (OSError, UnicodeError) as exc:
            raise InvalidURLError(
                "The domain could not be resolved to a public address."
            ) from exc

        addresses = []
        for record in records:
            try:
                addresses.append(
                    ipaddress.ip_address(record[4][0].split("%", 1)[0])
                )
            except (ValueError, IndexError, TypeError):
                continue

    # Reject the entire host if even one DNS answer is non-public. This is
    # intentionally conservative when a domain has mixed public/private answers.
    if not addresses or any(not address.is_global for address in addresses):
        raise InvalidURLError(
            "Private or non-public network destinations cannot be scanned."
        )
    return normalized


def _error(result, code, message):
    result["error"] = {"code": code, "message": message}
    return result


def _close_response(response):
    """Close streamed responses; tolerate minimal response doubles in tests."""
    close = getattr(response, "close", None)
    if callable(close):
        close()


def scan_website(raw_url, timeout=TIMEOUT_SECONDS):
    """Scan one public website, following a small, validated redirect chain."""
    result = {
        "scan_type": "live",
        "ok": False,
        "url": None,
        "status_code": None,
        "response_time_ms": None,
        "final_url": None,
        "uses_https": None,
        "redirect_count": 0,
        "security_headers": [],
        "error": None,
    }

    try:
        current_url = _validate_public_destination(raw_url)
    except InvalidURLError as error:
        return _error(result, "invalid_url", str(error))

    result["url"] = current_url
    start = time.perf_counter()

    try:
        for hop in range(MAX_REDIRECTS + 1):
            # Revalidate each hop immediately before making its request.
            current_url = _validate_public_destination(current_url)
            response = requests.get(
                current_url,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
                # Ignore environment proxy variables so the scan does not
                # silently route through an untrusted or internal proxy.
                proxies={"http": "", "https": ""},
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,*/*;q=0.5",
                },
            )

            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                _close_response(response)
                if not location:
                    return _error(
                        result,
                        "redirect_error",
                        "The website returned a redirect without a destination.",
                    )
                if hop >= MAX_REDIRECTS:
                    return _error(
                        result,
                        "too_many_redirects",
                        "The website redirected too many times.",
                    )
                try:
                    current_url = _validate_public_destination(
                        urljoin(current_url, location)
                    )
                except InvalidURLError as error:
                    return _error(result, "unsafe_redirect", str(error))
                result["redirect_count"] += 1
                continue

            result.update(
                {
                    "ok": True,
                    "status_code": response.status_code,
                    "response_time_ms": round(
                        (time.perf_counter() - start) * 1000
                    ),
                    "final_url": response.url,
                    "uses_https": urlparse(response.url).scheme.lower() == "https",
                    "security_headers": [
                        {
                            "name": name,
                            "present": name in response.headers,
                            "explanation": explanation,
                        }
                        for name, explanation in SECURITY_HEADERS.items()
                    ],
                }
            )
            _close_response(response)
            return result

    except requests.exceptions.Timeout:
        return _error(result, "timeout", "The website took too long to respond.")
    except requests.exceptions.SSLError:
        return _error(result, "ssl_error", "The HTTPS certificate check failed.")
    except requests.exceptions.ConnectionError:
        return _error(
            result,
            "connection_failed",
            "Could not connect. The site may be down or unreachable.",
        )
    except requests.exceptions.RequestException:
        return _error(result, "request_failed", "The website request failed.")

    return _error(result, "request_failed", "The scan could not be completed.")
