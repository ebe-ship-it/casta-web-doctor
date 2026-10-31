import sys
import time
from urllib.parse import urlparse

import requests


def check_website(url):
    if not url.startswith(("https://", "http://")):
        url = "https://" + url

    parsed = urlparse(url)

    if not parsed.hostname:
        print("Error: Invalid website address.")
        return

    if parsed.scheme not in ("http", "https"):
        print("Error: Only HTTP and HTTPS are supported.")
        return

    print(f"\nCASTA WEB DOCTOR")
    print("=" * 35)
    print(f"Website: {url}")

    try:
        start = time.perf_counter()

        response = requests.get(
            url,
            timeout=15,
            allow_redirects=True,
            headers={"User-Agent": "CastaWebDoctor/0.1"}
        )

        elapsed = (time.perf_counter() - start) * 1000

        print(f"Status code: {response.status_code}")
        print(f"Response time: {elapsed:.0f} ms")
        print(f"Final URL: {response.url}")

        print("\nHTTPS CHECK")
        if response.url.startswith("https://"):
            print("PASS: Final connection uses HTTPS.")
        else:
            print("WARNING: Final connection does not use HTTPS.")

        print("\nSECURITY HEADER CHECK")

        headers_to_check = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Content-Type-Options",
            "Referrer-Policy",
        ]

        for header in headers_to_check:
            if header in response.headers:
                print(f"PASS: {header}")
            else:
                print(f"INFO: {header} not detected")

        print("\nNOTE")
        print("Missing headers are not automatically proof of")
        print("a vulnerability. Results require context.")

    except requests.exceptions.Timeout:
        print("ERROR: The website took too long to respond.")

    except requests.exceptions.SSLError:
        print("ERROR: The HTTPS certificate check failed.")

    except requests.exceptions.RequestException as error:
        print(f"ERROR: Could not check website: {error}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py https://example.com")
        sys.exit(1)

    check_website(sys.argv[1])
