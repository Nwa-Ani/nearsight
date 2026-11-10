import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from agent.server import Handler


def _serve():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd


def test_health_and_demo():
    httpd = _serve()
    port = httpd.server_address[1]
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as r:
            health = json.load(r)
        assert health["ok"] is True
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/demo", timeout=5) as r:
            demo = json.load(r)
        assert demo["demo"] is True
        assert len(demo["items"]) >= 2
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as r:
            html = r.read().decode()
        assert "NearSight" in html
        assert "wallet connect" in html.lower() or "No wallet connect" in html
    finally:
        httpd.shutdown()
