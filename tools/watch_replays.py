#!/usr/bin/env python3
"""Watch the packaged 108 saved 3D encounters; no simulation is executed.

Run ``python tools/watch_replays.py`` from any directory. In a notebook::

    from tools.watch_replays import start_viewer
    viewer = start_viewer(port=0)
    print(viewer.url)
    # viewer.close() when finished

Only Python, NumPy, and a current web browser are required. No native model
build, video package, external JavaScript library, or pre-export is needed.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
from urllib.parse import urlencode, urlsplit
import webbrowser


@dataclass
class Viewer:
    """A running local viewer, including notebook-friendly cleanup."""
    url: str
    server: ThreadingHTTPServer
    thread: threading.Thread

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def start_viewer(*, port=8765, open_browser=True, case_id=None, single=False):
    """Serve saved runs on loopback, returning a Viewer with URL and close().

    Set port=0 for an automatically selected free port. The server loads only
    selected trajectories, checks their accounting, and keeps two in memory.
    """
    if not 0 <= port <= 65535:
        raise ValueError("Port must be between 0 and 65535")
    try:
        if __package__:
            from .replay_viewer.loader import build_catalog, load_case
        else:
            from replay_viewer.loader import build_catalog, load_case
    except ModuleNotFoundError as error:
        if error.name == "numpy":
            raise RuntimeError("NumPy is required. Install: python -m pip install -r requirements-analysis.txt") from error
        raise
    bundle = build_catalog()
    cases = {row["id"]: row for row in bundle["scenarios"]}
    if case_id is not None and case_id not in cases:
        raise ValueError("Unknown saved case: " + case_id)
    encoded_catalog = json.dumps(bundle, separators=(",", ":"), allow_nan=False)
    template = (Path(__file__).resolve().parent / "replay_viewer/browser.html").read_text()
    html = template.replace("__REPLAY_DATA__", encoded_catalog.replace("<", "\\u003c")).encode()
    cache = OrderedDict()
    cache_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def send_bytes(self, body, content_type, status=200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if self.command != "HEAD":
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

        def do_GET(self):
            path = urlsplit(self.path).path
            if path in ("/", "/index.html"):
                return self.send_bytes(html, "text/html; charset=utf-8")
            if path == "/api/catalog":
                return self.send_bytes(encoded_catalog.encode(), "application/json; charset=utf-8")
            if path == "/health":
                return self.send_bytes(b'{"status":"ready","saved_runs":108,"simulation_executed":false}', "application/json")
            match = re.fullmatch(r"/data/([A-Za-z0-9_-]+)\.js", path)
            if match and match[1] in cases:
                case = match[1]
                try:
                    with cache_lock:
                        if case in cache:
                            body = cache.pop(case)
                        else:
                            meta = cases[case]
                            payload = load_case(meta["source"], meta)
                            body = ("window.registerFishSimRun(" + json.dumps(case) + "," +
                                    json.dumps(payload, separators=(",", ":"), allow_nan=False) + ");\n").encode()
                        cache[case] = body
                        while len(cache) > 2:
                            cache.popitem(last=False)
                    return self.send_bytes(body, "text/javascript; charset=utf-8")
                except Exception as error:
                    return self.send_bytes(("Saved replay validation failed: " + str(error)).encode(), "text/plain; charset=utf-8", 500)
            return self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)

        do_HEAD = do_GET

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    query = {}
    if case_id:
        query["a"] = case_id
    if single:
        query["mode"] = "single"
    url = f"http://127.0.0.1:{server.server_port}/" + ("?" + urlencode(query) if query else "")
    thread = threading.Thread(target=server.serve_forever, name="saved-replay-viewer", daemon=True)
    thread.start()
    viewer = Viewer(url, server, thread)
    if open_browser:
        webbrowser.open(url)
    return viewer


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8765, help="Local port (default: 8765; 0 chooses a free port)")
    parser.add_argument("--no-browser", action="store_true", help="Print the URL without opening a browser")
    parser.add_argument("--case", dest="case_id", help="Start with this declared saved case ID as A")
    parser.add_argument("--single", action="store_true", help="Initially watch only A (comparison remains available)")
    args = parser.parse_args(argv)
    try:
        viewer = start_viewer(port=args.port, open_browser=not args.no_browser, case_id=args.case_id, single=args.single)
    except (ValueError, RuntimeError, OSError) as error:
        parser.exit(1, f"{error}\n")
    print("108 completed saved encounters; no simulation executed", flush=True)
    print(viewer.url, flush=True)
    print("Keep this process running. Press Ctrl+C to stop.", flush=True)
    try:
        viewer.thread.join()
    except KeyboardInterrupt:
        pass
    finally:
        viewer.close()


if __name__ == "__main__":
    main()
