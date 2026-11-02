#!/usr/bin/env python3
"""Build once and preview locally. Never compiles the PDF, commits, or publishes."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import webbrowser

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open", action="store_true", help="open the preview in your default browser")
    parser.add_argument("--version", choices=("main", "experimental"), default="main")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    with ExitStack() as stack:
        directory, route = ROOT, "/"
        handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
        try:
            server = stack.enter_context(ThreadingHTTPServer(("127.0.0.1", args.port), handler))
        except OSError as error:
            print(f"Cannot start preview on port {args.port}: {error}", file=sys.stderr)
            print("If a preview is already running, use its URL; otherwise try --port 4174.", file=sys.stderr)
            return 1
        builder = ROOT / ("experimental/build.py" if args.version == "experimental" else "build.py")
        result = subprocess.run([sys.executable, str(builder)], cwd=ROOT)
        if result.returncode:
            return result.returncode
        route = "/experimental/" if args.version == "experimental" else "/"
        url = f"http://127.0.0.1:{server.server_port}{route}"
        print(f"\n{args.version.capitalize()} website: {url}", flush=True)
        print("Keep this terminal open while viewing; Ctrl+C stops the preview.", flush=True)
        command = "python3 experimental/build.py" if args.version == "experimental" else "python3 build.py"
        print(f"After editing source, run {command} and refresh your browser.\n", flush=True)
        if args.open:
            try:
                webbrowser.open(url)
            except webbrowser.Error:
                print(f"Open {url} in your browser.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nPreview stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
