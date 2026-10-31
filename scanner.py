"""Casta Web Doctor scanner.

This module only collects data and returns it. It does not print.
"""

import time
from urllib.parse import urlparse

import requests

USER_AGENT = "CastaWebDoctor/0.2"
TIMEOUT_SECONDS = 15
MAX_URL_LENGTH = 2048

SECURITY_HEADERS = {
    "Strict-Transport-Security": "Tells browsers to always use HTTPS for this site.",
    "Content-Security-Policy": "Limits where scripts and other content can load from. Helps against cross-site scripting.",
    "X-Content-Type-Options": "Stops browsers from guessing file types. It should be set to nosniff.",
    "Referrer-Policy": "Controls how much page address information is shared when users click links.",
}


class InvalidURLError(ValueError):
    """Raised when the website address cannot be used."""


def normalize_url(raw_url):
    """Return a clean http/https URL, or raise InvalidURLError."""
    url = (raw_url or "").strip()

    if not url or len(url) > MAX_URL_LENGTH or any(c.isspace() for c in url):
        raise InvalidURLError("Invalid website address.")

    if "://" in url:
        scheme = url.split("://", 1)[0].lower()
        if scheme not in ("http", "https"):
            raise InvalidURLError("Only HTTP and HTTPS are supported.")
    else:
        url = "https://" + url

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        parsed.port  # raises ValueError if the port is bad
    except ValueError:
        raise InvalidURLError("Invalid website address.")

    if not hostname:
        raise InvalidURLError("Invalid website address.")

    return url


def _error(result, code, message):
    result["error"] = {"code": code, "message": message}
    return result


def scan_website(raw_url, timeout=TIMEOUT_SECONDS):
    """Scan one website and return a result dictionary.

    Every result is a real scan ("scan_type": "live").
    On failure, "ok" is False and "error" explains why.
    """
    result = {
        "scan_type": "live",
        "ok": False,
        "url": None,
        "status_code": None,
        "response_time_ms": None,
        "final_url": None,
        "uses_https": None,
        "security_headers": [],
        "error": None,
    }

    try:
        url = normalize_url(raw_url)
    except InvalidURLError as error:
        return _error(result, "invalid_url", str(error))

    result["url"] = url

    try:
        start = time.perf_counter()
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
    except requests.exceptions.Timeout:
        return _error(result, "timeout", "The website took too long to respond.")
    except requests.exceptions.SSLError:
        return _error(result, "ssl_error", "The HTTPS certificate check failed.")
    except requests.exceptions.ConnectionError:
        return _error(
            result,
            "connection_failed",
            "Could not connect. The address may be wrong, or the site may be down.",
        )
    except requests.exceptions.RequestException as error:
        return _error(result, "request_failed", f"Could not check website: {error}")

    result["ok"] = True
    result["status_code"] = response.status_code
    result["response_time_ms"] = round(elapsed_ms)
    result["final_url"] = response.url
    result["uses_https"] = response.url.startswith("https://")
    result["security_headers"] = [
        {
            "name": name,
            "present": name in response.headers,
            "explanation": explanation,
        }
        for name, explanation in SECURITY_HEADERS.items()
    ]
    return result

