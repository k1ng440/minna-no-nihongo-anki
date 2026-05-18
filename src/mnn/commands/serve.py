"""mnn serve — local static server for docs/."""
import http.server
import socketserver
import webbrowser
from functools import partial

from mnn import log
from mnn.config import settings
from mnn.paths import ROOT

logger = log.get(__name__)

DOCS = ROOT / "docs"
FALLBACK_PORTS = (8765, 8766, 8000, 3000, 5173, 0)


def _bind(handler, preferred: int | None) -> socketserver.ThreadingTCPServer:
    cfg_port = settings().serve_port
    candidates = []
    if preferred is not None:
        candidates.append(preferred)
    if cfg_port not in candidates:
        candidates.append(cfg_port)
    for p in FALLBACK_PORTS:
        if p not in candidates:
            candidates.append(p)
    last_err: OSError | None = None
    for p in candidates:
        try:
            httpd = socketserver.ThreadingTCPServer(("", p), handler)
            httpd.allow_reuse_address = True
            return httpd
        except OSError as e:
            last_err = e
            logger.warning("port %d busy: %s", p, e)
    raise last_err or OSError("no port available")


def run(port: int | None = None, open_browser: bool = True) -> None:
    if not DOCS.exists() or not (DOCS / "index.html").exists():
        logger.error("docs/ missing — run `mnn web` first")
        return
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(DOCS))
    httpd = _bind(handler, port)
    actual = httpd.server_address[1]
    url = f"http://localhost:{actual}/"
    logger.info("serving %s at %s", DOCS, url)
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("shutting down")
    finally:
        httpd.server_close()
