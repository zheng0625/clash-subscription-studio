import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from fastapi.testclient import TestClient

from app.engine import empty_edits, parse_config
from app.main import SUBSCRIPTION_USER_AGENT, create_app
from test_engine import DEMO

HEADERS = {"X-Clash-Studio": "1"}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path)) as value:
        yield value


def create(client, source_type="file", **values):
    response = client.post("/api/subscriptions", headers=HEADERS, json={"title": "测试订阅", "source_type": source_type, **({"yaml": DEMO} if source_type == "file" else {}), **values})
    assert response.status_code == 201, response.text
    return response.json()


def test_preview_save_persistence_and_history(client, tmp_path):
    detail = create(client)
    base = f"/api/subscriptions/{detail['id']}"
    edits = empty_edits()
    edits["proxy_renames"] = {"香港 01": "自定义香港"}
    body = {"revision": detail["revision"], "edits": edits}
    assert "自定义香港" in client.post(base + "/preview", headers=HEADERS, json=body).json()["yaml"]
    assert "自定义香港" not in client.get(detail["subscription_path"]).text
    saved = client.put(base + "/edits", headers=HEADERS, json=body).json()
    assert "自定义香港" in client.get(saved["subscription_path"]).text
    assert client.put(base + "/edits", headers=HEADERS, json=body).status_code == 409
    versions = client.get(base + "/history").json()
    assert len(versions) == 2
    restored = client.post(base + f"/history/{versions[-1]['id']}/restore", headers=HEADERS, json={"revision": saved["revision"]}).json()
    assert not restored["edits"]["proxy_renames"]
    # Reopen the SQLite database through a fresh application instance.
    with TestClient(create_app(tmp_path)) as reopened:
        assert reopened.get(base).json()["revision"] == restored["revision"]


def test_failed_refresh_keeps_published_and_conflicts_recover(client):
    detail = create(client)
    base = f"/api/subscriptions/{detail['id']}"
    edits = empty_edits()
    edits["group_overrides"] = {"流媒体": {"proxies": ["日本 01"]}}
    saved = client.put(base + "/edits", headers=HEADERS, json={"revision": detail["revision"], "edits": edits}).json()
    published = client.get(saved["subscription_path"]).text
    updated = DEMO.replace("日本 01", "日本 02")
    conflict = client.post(base + "/refresh", headers=HEADERS, json={"revision": saved["revision"], "yaml": updated}).json()
    assert conflict["preview"]["errors"]
    assert conflict["last_error"]
    assert client.get(saved["subscription_path"]).text == published
    edits["group_overrides"] = {}
    fixed = client.put(base + "/edits", headers=HEADERS, json={"revision": conflict["revision"], "edits": edits}).json()
    assert not fixed["last_error"]
    assert "日本 02" in client.get(saved["subscription_path"]).text
    bad = client.post(base + "/refresh", headers=HEADERS, json={"revision": fixed["revision"], "yaml": "<html>bad</html>"})
    assert bad.status_code == 400
    assert "日本 02" in client.get(saved["subscription_path"]).text


def test_real_http_subscription_refresh_and_upstream_headers(client):
    state = {"body": DEMO, "status": 200}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(state["status"])
            self.send_header("Subscription-Userinfo", "upload=0; download=10; total=100")
            self.end_headers()
            self.wfile.write(state["body"].encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        detail = create(client, "url", source_url=f"http://127.0.0.1:{server.server_port}/sub?token=test-only")
        base = f"/api/subscriptions/{detail['id']}"
        edits = empty_edits()
        edits["added_rules"] = ["DOMAIN,custom.example,DIRECT"]
        edits["rule_order"] = edits["added_rules"] + list(parse_config(DEMO)["rules"])
        saved = client.put(base + "/edits", headers=HEADERS, json={"revision": detail["revision"], "edits": edits}).json()
        state["body"] = DEMO.replace("  - MATCH,节点选择", "  - DOMAIN,upstream.example,DIRECT\n  - MATCH,节点选择")
        refreshed = client.post(base + "/refresh", headers=HEADERS, json={"revision": saved["revision"]}).json()
        response = client.get(detail["subscription_path"])
        assert response.status_code == 200
        assert response.headers["subscription-userinfo"] == "upload=0; download=10; total=100"
        assert "custom.example" in response.text and "upstream.example" in response.text
        state["status"] = 503
        failed = client.post(base + "/refresh", headers=HEADERS, json={"revision": refreshed["revision"]})
        assert failed.status_code == 400
        assert "test-only" not in failed.text
        assert client.get(detail["subscription_path"]).text == response.text
    finally:
        server.shutdown()
        server.server_close()


def test_invalid_save_does_not_publish_and_api_guards(client):
    detail = create(client)
    base = f"/api/subscriptions/{detail['id']}"
    old = client.get(detail["subscription_path"]).text
    edits = empty_edits()
    edits["deleted_groups"] = ["节点选择"]
    response = client.put(base + "/edits", headers=HEADERS, json={"revision": detail["revision"], "edits": edits})
    assert response.status_code == 422
    assert client.get(detail["subscription_path"]).text == old
    assert client.post("/api/subscriptions", json={}).status_code == 403
    assert client.post("/api/subscriptions", headers={**HEADERS, "Origin": "https://evil.example"}, json={}).status_code == 403
    assert client.get("/api/health", headers={"Host": "evil.example"}).status_code == 400


def test_rotate_disable_head_delete_and_cascade(client):
    detail = create(client)
    base = f"/api/subscriptions/{detail['id']}"
    assert client.head(detail["subscription_path"]).status_code == 200
    assert client.head(detail["subscription_path"]).headers["content-length"] == client.get(detail["subscription_path"]).headers["content-length"]
    rotated = client.post(base + "/rotate-token", headers=HEADERS, json={"revision": detail["revision"]}).json()
    assert client.get(detail["subscription_path"]).status_code == 404
    disabled = client.patch(base, headers=HEADERS, json={"revision": rotated["revision"], "title": "关闭", "enabled": False, "interval_minutes": 60}).json()
    assert client.get(rotated["subscription_path"]).status_code == 404
    assert client.delete(base, headers=HEADERS, params={"revision": disabled["revision"]}).status_code == 200
    assert client.get(base).status_code == 404
    assert client.get("/api/subscriptions").json() == []


def test_automatic_refresh_reapplies_edits(client):
    state = {"body": DEMO}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(state["body"].encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        detail = create(client, "url", source_url=f"http://127.0.0.1:{server.server_port}/sub")
        edits = empty_edits()
        edits["proxy_renames"] = {"香港 01": "自动刷新保留改名"}
        saved = client.put(f"/api/subscriptions/{detail['id']}/edits", headers=HEADERS, json={"revision": detail["revision"], "edits": edits}).json()
        client.app.state.store.update(detail["id"], saved["revision"], {"interval_minutes": 1, "refreshed_at": "2000-01-01T00:00:00+00:00"})
        state["body"] = DEMO.replace("  - MATCH,节点选择", "  - DOMAIN,scheduled.example,DIRECT\n  - MATCH,节点选择")
        deadline = time.monotonic() + 36
        while time.monotonic() < deadline:
            row = client.app.state.store.get(detail["id"])
            if "scheduled.example" in row["published"]:
                assert "自动刷新保留改名" in row["published"]
                assert not row["last_error"]
                break
            time.sleep(0.2)
        else:
            pytest.fail("Automatic refresh did not publish within one scheduler tick")
    finally:
        server.shutdown()
        server.server_close()


def test_subscription_client_identification_and_notice_preserves_published(client):
    notice = '''proxies: []
proxy-groups:
  - name: 提示
    type: select
    proxies: [请下载Clash Verge for windows]
rules: ["MATCH,DIRECT"]
'''
    state = {"notice": False, "agents": []}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            agent = self.headers.get("User-Agent", "")
            state["agents"].append(agent)
            body = DEMO if agent == "clash-verge/v2.5.8" and not state["notice"] else notice
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/sub?token=private-test-token"
        detail = create(client, "url", source_url=url)
        assert state["agents"] == [SUBSCRIPTION_USER_AGENT]
        published = client.get(detail["subscription_path"]).text
        assert "hk1.example.com" in published
        state["notice"] = True
        failed = client.post(f"/api/subscriptions/{detail['id']}/refresh", headers=HEADERS, json={"revision": detail["revision"]})
        assert failed.status_code == 400
        assert "没有提供实际节点" in failed.json()["detail"]
        assert "private-test-token" not in failed.text
        assert client.get(detail["subscription_path"]).text == published
        result = client.post("/api/subscriptions", headers=HEADERS, json={"title": "错误订阅", "source_type": "url", "source_url": url})
        assert result.status_code == 502
        assert len(client.get("/api/subscriptions").json()) == 1
    finally:
        server.shutdown()
        server.server_close()
