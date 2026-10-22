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
import os
import multiprocessing
import sys

from app.paths import instance_id, default_data_dir
from app.version import VERSION

if getattr(sys, "frozen", False) and sys.stdout is None:
    default_data_dir().mkdir(parents=True, exist_ok=True)
    sys.stdout = sys.stderr = (default_data_dir() / "startup.log").open("a", encoding="utf-8", buffering=1)

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
    multiprocessing.freeze_support()
    parser = argparse.ArgumentParser(description="Clash Studio local subscription workbench")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--stop", action="store_true", help="Stop this installation's running service")
    parser.add_argument("--data-dir", help="Override the persistent data directory")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args()
    if args.data_dir:
        os.environ["CLASH_STUDIO_DATA"] = str(Path(args.data_dir).expanduser().resolve())
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    url = f"http://127.0.0.1:{args.port}"
    if args.stop:
        try:
            with LOCAL_HTTP.open(url + "/api/health", timeout=3) as response:
                health = json.load(response)
            if health.get("app") != "clash-studio" or health.get("instance") != instance_id():
                raise SystemExit("This port belongs to another installation. Nothing was stopped.")
            request = urllib.request.Request(url + "/api/shutdown", data=b"{}", method="POST",
                                             headers={"X-Clash-Studio": "1", "Content-Type": "application/json"})
            with LOCAL_HTTP.open(request, timeout=5):
                print("Clash Studio is stopping.")
        except OSError:
            print("Clash Studio is not running or could not be stopped on this port.")
            raise SystemExit(1)
        raise SystemExit(0)
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", args.port))
        except OSError:
            try:
                with LOCAL_HTTP.open(url + "/api/health", timeout=2) as response:
                    health = json.load(response)
                if health.get("app") == "clash-studio" and health.get("instance") == instance_id():
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
    print(f"Data: {default_data_dir()}")
    from app.main import app
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port, access_log=False))
    app.state.shutdown_callback = lambda: setattr(server, "should_exit", True)
    server.run()
