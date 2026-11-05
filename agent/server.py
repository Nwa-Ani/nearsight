"""Free-tier web UI + JSON API. No wallet connect, no sign-up, no keys.

Bind 0.0.0.0:$PORT for Render. Stdlib only.
"""
from __future__ import annotations

import json
import os
import pathlib
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .risk_agent import run as run_agent

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DEMO_TOKENS = [
    "wrap.near",
    "usdt.tether-token.near",
    "token.rhealab.near",
]


def _json(handler, code, obj):
    body = json.dumps(obj, indent=2).encode()
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def _file(handler, path, content_type):
    data = path.read_bytes()
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class Handler(BaseHTTPRequestHandler):
    server_version = "wagmi-meme-agent-near/1.0"

    def log_message(self, fmt, *args):
        print(f"[http] {self.address_string()} {fmt % args}", flush=True)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = urllib.parse.parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            return _file(self, WEB / "index.html", "text/html; charset=utf-8")
        if path == "/health":
            return _json(self, 200, {"ok": True, "service": "wagmi-meme-agent-near"})
        if path == "/api/demo":
            # Offline fixtures via risk_agent path? Use CLI demo fixtures for speed.
            from .cli import FIX
            from .analyzer import analyze, roast

            items = []
            for p in sorted(FIX.glob("*.json")):
                snap = json.loads(p.read_text())
                mk = snap.pop("market", None)
                report = analyze(snap, mk)
                items.append({"fixture": p.name, "report": report, "roast": roast(report)})
            return _json(self, 200, {"demo": True, "items": items})
        if path == "/api/analyze":
            token = (qs.get("token") or [""])[0].strip()
            network = (qs.get("network") or ["mainnet"])[0].strip() or "mainnet"
            if network not in ("mainnet", "testnet"):
                return _json(self, 400, {"error": "network must be mainnet or testnet"})
            if not token:
                return _json(self, 400, {"error": "token query param required", "example": "/api/analyze?token=wrap.near&network=mainnet"})
            holders = None
            if qs.get("holders"):
                holders = [h for h in qs["holders"][0].split(",") if h]
            try:
                limit = int((qs.get("limit") or ["25"])[0])
            except ValueError:
                limit = 25
            limit = max(1, min(limit, 50))
            result = run_agent(token, network=network, holders=holders, holder_limit=limit)
            code = 200 if "error" not in result else 502
            return _json(self, code, result)
        if path == "/api/examples":
            return _json(
                self,
                200,
                {
                    "analyze": "/api/analyze?token=wrap.near&network=mainnet",
                    "demo": "/api/demo",
                    "suggested_mainnet_tokens": DEMO_TOKENS,
                    "note": "Read-only. No wallet connect. No sign-up.",
                },
            )
        self.send_error(404, "Not found")


def main():
    port = int(os.environ.get("PORT", "8080"))
    host = os.environ.get("HOST", "0.0.0.0")
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"wagmi-meme-agent-near listening on http://{host}:{port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
