#!/usr/bin/env python3
"""Serve every lesson locally, with HTTP range requests so the videos can seek.

    python3 lessonkit/serve.py          # then open http://localhost:8710
    python3 lessonkit/serve.py 9000     # another port

The front page lists the lessons (folders with a lesson.json and a built web/ player).
"""
import html
import json
import os
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent


def lessons():
    for meta in sorted(PROJECT.glob("*/lesson.json")):
        info = json.loads(meta.read_text())
        if (meta.parent / "web" / "index.html").exists():
            yield meta.parent.name, info.get("title", meta.parent.name), info.get("subtitle", "")


def index_page() -> bytes:
    items = "".join(
        f'<li><a href="/{html.escape(folder)}/web/">{html.escape(title)}</a>'
        f'<span>{html.escape(sub)}</span></li>' for folder, title, sub in lessons())
    return f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lessons</title>
<style>
:root{{--bg:#EDF1F0;--ink:#172027;--muted:#55616A;--accent:#1A6F90;--rule:#CBD5D8}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0A0C0F;--ink:#E5E9EC;--muted:#96A1AB;--accent:#58C4DD;--rule:#262D35;color-scheme:dark}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif;padding:48px max(16px,env(safe-area-inset-left))}}
main{{max-width:640px;margin:0 auto}} h1{{font:600 2rem/1.2 Georgia,serif;margin:0 0 20px}}
ul{{list-style:none;padding:0;margin:0;display:grid;gap:2px}} li{{display:grid;padding:12px 0;border-bottom:1px solid var(--rule)}}
a{{color:var(--accent);font-weight:600;font-size:1.1rem;text-decoration:none}} a:hover{{text-decoration:underline}}
span{{color:var(--muted);font-size:.92rem}}
</style><main><h1>Lessons</h1><ul>{items}</ul></main>""".encode()


class RangeHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = index_page()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def send_head(self):
        path = self.translate_path(self.path)
        m = re.match(r"bytes=(\d*)-(\d*)$", self.headers.get("Range", ""))
        if not m or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2) or 0))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            self.send_error(416, "Requested range not satisfiable")
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        self._remaining = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        try:
            while remaining > 0:
                chunk = source.read(min(64 * 1024, remaining))
                if not chunk:
                    break
                outputfile.write(chunk)
                remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass  # the browser often cancels a range it no longer needs

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8710
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(RangeHandler, directory=str(PROJECT)))
    print(f"Serving the lessons at http://localhost:{port}")
    server.serve_forever()
