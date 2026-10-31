"""Small mobile-friendly web interface for Casta Web Doctor."""
import os
from flask import Flask, jsonify, render_template, request
from scanner import scan_website

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024
app.config["JSON_SORT_KEYS"] = False

@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/scan")
def api_scan():
    if not request.is_json:
        return jsonify({"ok": False, "error": {"code": "invalid_request", "message": "Send a JSON request."}}), 415
    payload = request.get_json(silent=True) or {}
    url = payload.get("url", "")
    if not isinstance(url, str) or len(url) > 2048:
        return jsonify({"ok": False, "error": {"code": "invalid_url", "message": "Enter a valid website address."}}), 400
    result = scan_website(url)
    if not result["ok"]:
        status = 400 if result["error"]["code"] in ("invalid_url", "unsafe_redirect") else 502
        return jsonify(result), status
    return jsonify(result)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "Casta Web Doctor"})


if __name__ == "__main__":
    # Set CASTA_HOST=127.0.0.1 for local-only access. Use a production WSGI
    # server (for example gunicorn) in deployment, not Flask's dev server.
    app.run(host=os.environ.get("CASTA_HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")), debug=False)
