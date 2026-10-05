#!/usr/bin/env python3
"""Loopback preview: expose only the generated dashboard, never repository files."""
import http.server
import webbrowser
from urllib.parse import urlsplit
import db
from build_dashboard import build_dashboard

PORT = 8080


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if urlsplit(self.path).path not in ('/','/index.html'):
            self.send_error(404)
            return
        content=(db.ROOT/'index.html').read_bytes()
        self.send_response(200)
        self.send_header('Content-Type','text/html; charset=utf-8')
        self.send_header('Content-Length',str(len(content)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(content)


def main():
    build_dashboard()
    with http.server.ThreadingHTTPServer(('127.0.0.1',PORT),Handler) as server:
        print(f'Dashboard: http://localhost:{PORT}')
        webbrowser.open(f'http://localhost:{PORT}/')
        try: server.serve_forever()
        except KeyboardInterrupt: pass


if __name__=='__main__': main()
