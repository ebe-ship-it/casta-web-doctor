import sys

from scanner import scan_website


def print_report(result):
    print("\nCASTA WEB DOCTOR")
    print("=" * 35)

    if result["url"]:
        print(f"Website: {result['url']}")

    if not result["ok"]:
        message = result["error"]["message"]
        if result["error"]["code"] == "invalid_url":
            print(f"Error: {message}")
        else:
            print(f"ERROR: {message}")
        return

    print(f"Status code: {result['status_code']}")
    print(f"Response time: {result['response_time_ms']} ms")
    print(f"Final URL: {result['final_url']}")

    print("\nHTTPS CHECK")
    if result["uses_https"]:
        print("PASS: Final connection uses HTTPS.")
    else:
        print("WARNING: Final connection does not use HTTPS.")

    print("\nSECURITY HEADER CHECK")
    for header in result["security_headers"]:
        if header["present"]:
            print(f"PASS: {header['name']}")
        else:
            print(f"INFO: {header['name']} not detected")
            print(f"      Why it matters: {header['explanation']}")

    print("\nNOTE")
    print("Missing headers are not automatically proof of")
    print("a vulnerability. Results require context.")


def check_website(url):
    print_report(scan_website(url))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py https://example.com")
        sys.exit(1)

    check_website(sys.argv[1])
