# Casta Web Doctor 🩺

Casta Web Doctor is a small Python website diagnostics tool with both a command-line scanner and a mobile-friendly web interface.

## Features

- HTTP status and response-time checks.
- HTTPS detection and redirect counting.
- Checks for common security headers.
- Mobile-friendly browser interface.
- JSON endpoint for programmatic scans.
- Basic SSRF protections: only HTTP(S), standard ports, public destinations, and a small manually validated redirect chain.
- Automated tests and GitHub Actions.

## Requirements

- Python 3.10+
- pip

## Install

```bash
git clone https://github.com/ebe-ship-it/casta-web-doctor.git
cd casta-web-doctor
python -m venv .venv
```

Activate the virtual environment:

- Linux/macOS/Termux: `source .venv/bin/activate`
- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`

Install packages:

```bash
python -m pip install -r requirements.txt
```

## Start the web app

```bash
python webapp.py
```

Open `http://127.0.0.1:5000` in your browser. The app listens on localhost by default. Set `PORT` to change the port.

The JSON API accepts a POST request to `/api/scan` with `Content-Type: application/json` and a body such as:

```json
{"url": "https://example.com"}
```

A simple health endpoint is available at `/health`.

## Command-line scanner

```bash
python main.py https://example.com
python main.py example.com
```

## Run tests

```bash
python -m pytest -v
```

## Security and deployment notes

This project is an early-stage diagnostic tool, not a full penetration test or a guarantee that a website is secure. Missing headers are not automatically vulnerabilities.

The scanner rejects loopback, private, link-local, reserved, and other non-public IP addresses, restricts destinations to HTTP(S) ports 80 and 443, and validates redirects individually. DNS can change between validation and connection, so production hosting should also apply network-level outbound firewall rules that block private/internal address ranges. Add request rate limits and abuse monitoring before exposing the scanner publicly. Do not deploy with Flask's development server; use a production WSGI server and a suitable reverse proxy.

Only scan websites you own or have permission to assess.

## Project status

Early development. The web UI and basic checks are implemented; additional SEO and link checks can be added after the security and test suite are reviewed.

## Author

**Casta** · [@ebe-ship-it](https://github.com/ebe-ship-it)
