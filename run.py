"""Local launcher. No subscription URLs are written to the console access log."""
import argparse
import hashlib
import json
from pathlib import Path
import socket
import threading
import time
import urllib.request
import webbrowser

import uvicorn

LOCAL_HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def open_when_ready(url):
    for _ in range(60):
        try:
            with LOCAL_HTTP.open(url + "/api/health", timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except OSError:
            time.sleep(0.25)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clash Studio local subscription workbench")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    url = f"http://127.0.0.1:{args.port}"
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", args.port))
        except OSError:
            try:
                with LOCAL_HTTP.open(url + "/api/health", timeout=2) as response:
                    health = json.load(response)
                instance = hashlib.sha256(str(Path(__file__).resolve().parent).casefold().encode()).hexdigest()[:16]
                if health.get("app") == "clash-studio" and health.get("instance") == instance:
                    if not args.no_browser:
                        webbrowser.open(url)
                    print(f"Clash Studio is already running: {url}")
                    raise SystemExit(0)
            except (OSError, ValueError):
                pass
            print(f"Port {args.port} is in use. Close the existing process or use --port <number>.")
            raise SystemExit(1)
    if not args.no_browser:
        threading.Thread(target=open_when_ready, args=(url,), daemon=True).start()
    print(f"Clash Studio: {url}\nKeep this window running. Press Ctrl+C to stop.")
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, access_log=False)
