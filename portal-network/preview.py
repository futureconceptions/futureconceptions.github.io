#!/usr/bin/env python3
"""Lokale Vorschau eines gebauten Portals.

    python3 portal-network/preview.py firmennachrichten.de           # dist/
    python3 portal-network/preview.py itszene.de --drafts --port 8001  # dist-preview/
    python3 portal-network/preview.py it-erfahrungen.de --test        # dist-test/

Danach im Browser: http://localhost:8000/
Absolute Links auf Schwesterportale (https://…) führen ins echte Internet.
"""
import argparse
import functools
import http.server
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent


class Handler(http.server.SimpleHTTPRequestHandler):
    def send_error(self, code, message=None, explain=None):
        if code == 404:
            page = pathlib.Path(self.directory) / "404.html"
            if page.is_file():
                data = page.read_bytes()
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(data)
                return
        super().send_error(code, message, explain)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("domain")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--drafts", action="store_true", help="dist-preview/ verwenden")
    g.add_argument("--test", action="store_true", help="dist-test/ verwenden")
    a = ap.parse_args()
    root = HERE / ("dist-preview" if a.drafts else "dist-test" if a.test else "dist") / a.domain
    if not root.is_dir():
        print(f"{root} existiert nicht – zuerst bauen: python3 portal-network/build.py"
              f"{' --drafts' if a.drafts else ' --test' if a.test else ''}", file=sys.stderr)
        return 1
    handler = functools.partial(Handler, directory=str(root))
    with http.server.ThreadingHTTPServer((a.host, a.port), handler) as srv:
        print(f"Vorschau {a.domain}: http://{a.host}:{a.port}/  (Strg+C beendet)")
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
