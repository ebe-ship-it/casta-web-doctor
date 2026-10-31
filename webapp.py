"""Small, production-oriented Flask interface for Casta Web Doctor."""
import os

from flask import Flask, jsonify, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.middleware.proxy_fix import ProxyFix

from scanner import scan_website

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024
app.config["JSON_SORT_KEYS"] = False

# Only trust forwarded client/protocol headers when running behind the configured
# hosting proxy. Never enable this when the app is directly exposed to clients.
if os.environ.get("TRUST_PROXY_HEADERS", "").lower() == "true":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# Set RATELIMIT_STORAGE_URI to a shared Redis URL in a multi-worker production
# deployment. The in-memory fallback is suitable only for a small beta.
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
    headers_enabled=True,
)


@app.after_request
def add_security_headers(response):
    """Set conservative browser protections for the app's own responses."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=(), payment=()",
    )
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'none'; "
        "style-src 'unsafe-inline'; "
        "script-src 'unsafe-inline'; "
        "connect-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "base-uri 'none'; "
        "form-action 'self'; "
        "frame-ancestors 'none'",
    )
    if request.path.startswith("/api/") or request.path == "/health":
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/scan")
@limiter.limit("20 per minute")
@limiter.limit("300 per day")
def api_scan():
    if not request.is_json:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "invalid_request",
                        "message": "Send a JSON request.",
                    },
                }
            ),
            415,
        )

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "invalid_request",
                        "message": "Send a JSON object containing a website address.",
                    },
                }
            ),
            400,
        )

    url = payload.get("url", "")
    if not isinstance(url, str) or len(url) > 2048:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "invalid_url",
                        "message": "Enter a valid website address.",
                    },
                }
            ),
            400,
        )

    result = scan_website(url)
    if not result["ok"]:
        status = (
            400
            if result["error"]["code"] in ("invalid_url", "unsafe_redirect")
            else 502
        )
        return jsonify(result), status
    return jsonify(result)


@app.errorhandler(429)
def handle_rate_limit(_error):
    if request.path.startswith("/api/"):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many scans in a short period. Please wait before trying again.",
                    },
                }
            ),
            429,
        )
    return "Too many requests. Please wait before trying again.", 429


@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(_error):
    if request.path.startswith("/api/"):
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "request_too_large",
                        "message": "The request is too large. Send a smaller JSON body.",
                    },
                }
            ),
            413,
        )
    return "Request too large.", 413


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "Casta Web Doctor"})


if __name__ == "__main__":
    # Set CASTA_HOST=127.0.0.1 for local-only access. Use a production WSGI
    # server (for example gunicorn) in deployment, not Flask's dev server.
    app.run(
        host=os.environ.get("CASTA_HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
