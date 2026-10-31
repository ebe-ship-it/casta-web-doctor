"""Casta Web Doctor's bounded website scanner.

The scanner only permits public HTTP(S) destinations on ports 80 and 443,
revalidates every redirect, limits redirects, and does not download page bodies.
For production deployments, network-level egress controls are still recommended:
DNS validation alone cannot completely eliminate DNS-rebinding races.
"""
import ipaddress
import socket
import time
from urllib.parse import urljoin, urlparse, urlunparse

import requests

USER_AGENT = "CastaWebDoctor/1.0"
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
    url = (raw_url or "").strip()
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

    if parsed.scheme.lower() not in ("http", "https"):
        raise InvalidURLError("Only HTTP and HTTPS addresses are supported.")
    if not hostname or parsed.username is not None or parsed.password is not None:
        raise InvalidURLError("That website address is not allowed.")
    if port is not None and port not in (80, 443):
        raise InvalidURLError("For safety, only standard HTTP/HTTPS ports are supported.")

    # Fragments are client-side only and should not be sent to the server.
    return urlunparse((parsed.scheme.lower(), parsed.netloc, parsed.path or "/", parsed.params, parsed.query, ""))


def _validate_public_destination(url):
    """Reject local, private, reserved, and non-public destinations."""
    normalized = normalize_url(url)
    parsed = urlparse(normalized)
    host = parsed.hostname.rstrip(".").lower()

    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise InvalidURLError("Local and internal network addresses cannot be scanned.")

    try:
        literal = ipaddress.ip_address(host)
        addresses = [literal]
    except ValueError:
        try:
            records = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except (OSError, socket.gaierror) as exc:
            raise InvalidURLError("The domain could not be resolved to a public address.") from exc
        addresses = []
        for record in records:
            try:
                addresses.append(ipaddress.ip_address(record[4][0].split("%", 1)[0]))
            except ValueError:
                continue

    if not addresses or any(not address.is_global for address in addresses):
        raise InvalidURLError("Private or non-public network destinations cannot be scanned.")
    return normalized


def _error(result, code, message):
    result["error"] = {"code": code, "message": message}
    return result


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
            # Validate each hop independently. Redirects are never followed
            # automatically because each destination must pass our checks.
            current_url = _validate_public_destination(current_url)
            response = requests.get(
                current_url,
                timeout=timeout,
                allow_redirects=False,
                stream=True,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.5"},
            )

            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                response.close()
                if not location:
                    return _error(result, "redirect_error", "The website returned a redirect without a destination.")
                if hop >= MAX_REDIRECTS:
                    return _error(result, "too_many_redirects", "The website redirected too many times.")
                try:
                    current_url = urljoin(current_url, location)
                    current_url = _validate_public_destination(current_url)
                except InvalidURLError as error:
                    return _error(result, "unsafe_redirect", str(error))
                result["redirect_count"] += 1
                continue

            elapsed_ms = round((time.perf_counter() - start) * 1000)
            result["ok"] = True
            result["status_code"] = response.status_code
            result["response_time_ms"] = elapsed_ms
            result["final_url"] = response.url
            result["uses_https"] = urlparse(response.url).scheme.lower() == "https"
            result["security_headers"] = [
                {
                    "name": name,
                    "present": name in response.headers,
                    "explanation": explanation,
                }
                for name, explanation in SECURITY_HEADERS.items()
            ]
            response.close()
            return result

    except requests.exceptions.Timeout:
        return _error(result, "timeout", "The website took too long to respond.")
    except requests.exceptions.SSLError:
        return _error(result, "ssl_error", "The HTTPS certificate check failed.")
    except requests.exceptions.ConnectionError:
        return _error(result, "connection_failed", "Could not connect. The site may be down or unreachable.")
    except requests.exceptions.RequestException:
        return _error(result, "request_failed", "The website request failed.")

    return _error(result, "request_failed", "The scan could not be completed.")
