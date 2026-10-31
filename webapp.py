"""Small mobile-friendly web interface for Casta Web Doctor."""
import os
from flask import Flask, jsonify, render_template_string, request
from scanner import scan_website

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024
app.config["JSON_SORT_KEYS"] = False

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0b1020">
<meta name="description" content="Check website availability, HTTPS, response time, redirects, and security headers with Casta Web Doctor.">
<title>Casta Web Doctor | Website Health Check</title>
<style>
:root{color-scheme:dark;--bg:#090d18;--panel:#111a2c;--line:#26344c;--muted:#9aabc5;--text:#f4f7ff;--blue:#80a9ff;--green:#5ee0ae;--amber:#ffd078;--red:#ff8e9b}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at top,#15284a 0,#090d18 55%);color:var(--text);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;min-height:100vh}
.wrap{width:min(920px,100%);margin:auto;padding:28px 18px 52px}.brand{display:flex;align-items:center;gap:12px;font-weight:800;letter-spacing:.02em}.logo{display:grid;place-items:center;width:42px;height:42px;border-radius:13px;background:#1d3154;border:1px solid #3a5683;color:var(--blue);font-size:23px}
.pill{font-size:12px;border:1px solid var(--line);border-radius:99px;padding:4px 9px;color:var(--muted);margin-left:auto}
.hero{padding:56px 0 28px}.eyebrow{color:var(--green);font-size:12px;font-weight:800;letter-spacing:.16em;text-transform:uppercase}h1{font-size:clamp(34px,7vw,58px);line-height:1.04;letter-spacing:-.045em;margin:12px 0 16px;max-width:700px}h1 span{color:var(--blue)}.lead{color:var(--muted);max-width:620px;margin:0}
.card{background:rgba(17,26,44,.94);border:1px solid var(--line);border-radius:22px;padding:22px;box-shadow:0 20px 70px #0002}.form{display:flex;gap:10px;margin-top:14px}.form input{min-width:0;flex:1;background:#0a1120;color:var(--text);border:1px solid #34435e;border-radius:12px;padding:15px;font:inherit;outline:none}.form input:focus{border-color:var(--blue);box-shadow:0 0 0 3px #80a9ff22}button{border:0;border-radius:12px;background:var(--blue);color:#071020;font-weight:800;font:inherit;padding:0 22px;cursor:pointer}button:disabled{opacity:.65;cursor:wait}.hint{color:var(--muted);font-size:12px;margin:10px 0 0}.error{margin-top:14px;padding:12px 14px;border-radius:12px;background:#3b1c2a;border:1px solid #743246;color:#ffdce1}
.results{margin-top:22px}.results h2{font-size:22px;margin:0 0 14px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.metric{border:1px solid var(--line);background:#0b1322;border-radius:14px;padding:15px;min-width:0}.label{color:var(--muted);font-size:12px}.value{font-size:23px;font-weight:800;overflow-wrap:anywhere;margin-top:4px}.sub{color:var(--muted);font-size:12px;overflow-wrap:anywhere}.section{margin-top:20px}.section h3{font-size:16px;margin:0 0 10px}.check{display:flex;gap:12px;align-items:flex-start;padding:13px 0;border-bottom:1px solid var(--line)}.check:last-child{border-bottom:0}.icon{width:26px;height:26px;flex:none;display:grid;place-items:center;border-radius:50%;font-weight:900}.pass{background:#123b31;color:var(--green)}.missing{background:#3b3020;color:var(--amber)}.check strong{display:block}.check p{color:var(--muted);font-size:13px;margin:3px 0 0}.note{font-size:12px;color:var(--muted);margin-top:18px}.footer{color:var(--muted);font-size:12px;text-align:center;margin-top:30px}
@media(max-width:600px){.wrap{padding:18px 14px 36px}.hero{padding:42px 0 22px}.card{padding:16px;border-radius:17px}.form{flex-direction:column}.form button{padding:14px}.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.value{font-size:20px}.pill{font-size:10px}}
</style></head>
<body><main class="wrap">
<header class="brand"><div class="logo">✚</div><div>CASTA<br><span style="font-size:12px;color:var(--muted);font-weight:600">WEB DOCTOR</span></div><div class="pill">PUBLIC BETA · 1.0</div></header>
<section class="hero"><div class="eyebrow">Website diagnostics</div><h1>Your website's<br><span>health check.</span></h1><p class="lead">A quick first look at availability, response time, HTTPS, redirects, and key security headers. Clear results, no jargon.</p></section>
<section class="card"><form id="scan-form"><label for="url"><strong>Website address</strong></label><div class="form"><input id="url" name="url" type="text" inputmode="url" placeholder="example.com" autocomplete="url" maxlength="2048" required><button id="scan-btn" type="submit">Scan website ↗</button></div><p class="hint">Only public websites on standard HTTP/HTTPS ports are supported. Don't scan a site without permission.</p><div id="error" class="error" hidden></div></form></section>
<section id="results" class="results card" hidden aria-live="polite"></section>
<p class="footer">CASTA WEB DOCTOR · Early development · Results are diagnostic hints, not a full security audit.</p>
</main>
<script>
const form=document.querySelector('#scan-form'),btn=document.querySelector('#scan-btn'),err=document.querySelector('#error'),results=document.querySelector('#results');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
form.addEventListener('submit',async e=>{e.preventDefault();err.hidden=true;results.hidden=true;btn.disabled=true;btn.textContent='Scanning…';
try{const res=await fetch('/api/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:form.url.value})});const data=await res.json();
if(!res.ok||!data.ok){err.textContent=data.error?.message||'The scan could not be completed.';err.hidden=false;return;}
const rows=data.security_headers.map(h=>'<div class="check"><div class="icon '+(h.present?'pass':'missing')+'">'+(h.present?'✓':'!')+'</div><div><strong>'+esc(h.name)+' · '+(h.present?'Detected':'Not detected')+'</strong><p>'+esc(h.explanation)+'</p></div></div>').join('');
const https=data.uses_https?'Yes':'No';
results.innerHTML='<h2>Scan report</h2><div class="sub">Requested: '+esc(data.url)+'</div><div class="grid" style="margin-top:14px"><div class="metric"><div class="label">HTTP status</div><div class="value">'+esc(data.status_code)+'</div><div class="sub">'+(data.status_code>=200&&data.status_code<400?'Responded successfully':'Check server response')+'</div></div><div class="metric"><div class="label">Response time</div><div class="value">'+esc(data.response_time_ms)+' ms</div><div class="sub">Includes redirect time</div></div><div class="metric"><div class="label">Uses HTTPS</div><div class="value">'+https+'</div><div class="sub">Final connection</div></div><div class="metric"><div class="label">Redirects</div><div class="value">'+esc(data.redirect_count)+'</div><div class="sub">Maximum 5</div></div><div class="metric" style="grid-column:span 2"><div class="label">Final address</div><div class="sub" style="margin-top:8px">'+esc(data.final_url)+'</div></div></div><div class="section"><h3>Security headers</h3>'+rows+'</div><p class="note">A missing header is not automatically a vulnerability. Check whether it is appropriate for the website before changing server settings.</p>';
results.hidden=false;
}catch(e){err.textContent='Could not reach the scanner. Check your connection and try again.';err.hidden=false;}
finally{btn.disabled=false;btn.textContent='Scan website ↗';}});
</script></body></html>"""


@app.get("/")
def index():
    return render_template_string(PAGE)


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
