# Casta Web Doctor

A lightweight website diagnostics tool with a standalone HTML/CSS/JavaScript interface, a Python scanner, and a command-line mode. The interface uses a restrained editorial visual style rather than a component framework or generated site builder.

## What it checks

- HTTP status and approximate response time.
- HTTPS on the final connection.
- Redirect count and final URL.
- Five common security headers, with plain-language explanations.
- A mobile-friendly results report and JSON API.
- Input validation, a bounded redirect chain, public-IP checks, response closing, basic response security headers, and API rate limits.

## Requirements

- Python 3.10 or newer
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

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Run locally

```bash
python webapp.py
```

Open `http://127.0.0.1:5000`. The development server binds to localhost by default. Set `PORT` to change the port.

For production, run the WSGI server rather than Flask's development server:

```bash
gunicorn webapp:app --workers 2 --threads 4 --timeout 30
```

## API

Send a JSON POST request to `/api/scan`:

```json
{"url": "https://example.com"}
```

The API returns a structured scan report. Invalid input returns a 4xx response; scan failures return a 502 response. `/health` is a simple health-check endpoint.

## Command-line scanner

```bash
python main.py https://example.com
python main.py example.com
```

## Tests

```bash
python -m pytest -v
```

GitHub Actions runs the test suite on pushes to `main` and pull requests.

## Security limitations

This is a first-pass diagnostic tool, not a penetration test and not a guarantee that a site is secure. Missing headers are not automatically vulnerabilities.

The scanner only accepts HTTP(S) and each scheme's standard port, rejects non-public IP addresses, and manually validates every redirect. DNS can change between validation and the actual HTTP connection, so DNS checks alone cannot eliminate DNS-rebinding SSRF. A production deployment must enforce outbound network rules that block loopback, private, link-local, metadata-service, and other internal destinations.

The API has per-IP limits of 20 requests per minute and 300 per day. The default limiter store is in-memory, which is suitable only for a small beta and is not shared across multiple workers or instances. The Render blueprint uses one worker so the in-memory limits are consistent within that service instance. For a public multi-worker deployment, configure a shared Redis-compatible store with the `RATELIMIT_STORAGE_URI` environment variable. The Render blueprint enables `TRUST_PROXY_HEADERS` only because the app is behind Render's proxy; do not enable that setting when exposing the app directly to the internet. Monitor abuse and apply hosting/network egress restrictions before opening the scanner to wider public use.

Only scan websites you own or have permission to assess.

## Deploy on Render

A `render.yaml` blueprint configures a Python web service, Gunicorn, and the `/health` health check.

1. Open [Render](https://render.com/) and choose **New → Blueprint**.
2. Connect `ebe-ship-it/casta-web-doctor` and select the `main` branch.
3. Review the service settings and create the service.
4. When deployment finishes, open the public `onrender.com` address and test `/health` and the scan form.

The repository being ready for deployment does not mean a live service has already been deployed. Free hosting may sleep while idle. Configure shared rate-limit storage and outbound network restrictions before treating this as a public scanning service.

## Author

**Casta** · [@ebe-ship-it](https://github.com/ebe-ship-it)
