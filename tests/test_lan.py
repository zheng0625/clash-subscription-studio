import json
import socket

import httpx
import pytest
from fastapi.testclient import TestClient

import app.lan as lan
from app.main import create_app
from test_engine import DEMO

HEADERS = {"X-Clash-Studio": "1"}
LOCAL_IP = "192.168.50.10"


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(lan, "lan_addresses", lambda: [{"address": LOCAL_IP, "preferred": True}, {"address": "192.168.50.11", "preferred": False}])
    app = create_app(tmp_path)
    with TestClient(app) as client:
        response = client.post("/api/subscriptions", headers=HEADERS, json={"title": "LAN 测试", "source_type": "file", "yaml": DEMO})
        assert response.status_code == 201
        yield app, client, response.json(), tmp_path


@pytest.mark.parametrize("address,allowed", [
    ("192.168.88.10", True), ("10.1.2.3", True), ("172.16.2.5", True),
    ("172.31.255.254", True), ("172.32.0.1", False), ("8.8.8.8", False),
    ("198.51.100.5", False), ("169.254.1.1", False), ("::1", False), ("not-an-ip", False),
])
def test_rfc1918_only(address, allowed):
    assert lan.is_lan_ipv4(address) is allowed


def test_lan_app_exposes_only_tokenised_subscriptions(fixture):
    app, local, detail, _ = fixture
    with TestClient(app.state.lan_app, base_url=f"http://{LOCAL_IP}:8767", client=("192.168.88.20", 50000)) as remote:
        response = remote.get(detail["subscription_path"])
        assert response.status_code == 200
        assert response.text == local.get(detail["subscription_path"]).text
        assert response.headers["cache-control"] == "no-store"
        assert remote.head(detail["subscription_path"]).headers["content-length"] == response.headers["content-length"]
        for path in ("/", "/api/subscriptions", "/api/network", "/api/health", "/docs", "/openapi.json"):
            result = remote.get(path)
            assert result.status_code == 404
            assert detail["id"] not in result.text and "password" not in result.text
        assert remote.post("/api/network", headers=HEADERS, json={"enabled": True}).status_code == 404
        assert remote.post(detail["subscription_path"], headers=HEADERS).status_code == 405
        assert remote.get("/sub/invalid-token").status_code == 404
        rotated = local.post(f"/api/subscriptions/{detail['id']}/rotate-token", headers=HEADERS, json={"revision": detail["revision"]}).json()
        assert remote.get(detail["subscription_path"]).status_code == 404
        assert remote.get(rotated["subscription_path"]).status_code == 200
        local.patch(f"/api/subscriptions/{detail['id']}", headers=HEADERS, json={"revision": rotated["revision"], "title": detail["title"], "enabled": False, "interval_minutes": 0})
        assert remote.get(rotated["subscription_path"]).status_code == 404


def test_public_clients_and_dns_rebinding_are_rejected(fixture):
    app, local, detail, _ = fixture
    with TestClient(app.state.lan_app, base_url=f"http://{LOCAL_IP}:8767", client=("203.0.113.5", 50000)) as remote:
        assert remote.get(detail["subscription_path"]).status_code == 403
        assert remote.get(detail["subscription_path"], headers={"X-Forwarded-For": "192.168.88.20"}).status_code == 403
    with TestClient(app.state.lan_app, base_url="http://evil.example", client=("192.168.88.20", 50000)) as remote:
        assert remote.get(detail["subscription_path"]).status_code == 400
    assert local.get("/api/subscriptions", headers={"Host": LOCAL_IP}).status_code == 400


def test_enable_change_port_disable_and_real_http_listener(fixture):
    app, client, detail, directory = fixture
    assert not client.get("/api/network").json()["enabled"]
    first_port, second_port = free_port(), free_port()
    enabled = client.put("/api/network", headers=HEADERS, json={"enabled": True, "port": first_port, "selected_host": LOCAL_IP})
    assert enabled.status_code == 200, enabled.text
    assert enabled.json()["running"]
    assert enabled.json()["base_url"] == f"http://{LOCAL_IP}:{first_port}"
    with httpx.Client(trust_env=False) as remote:
        assert remote.get(f"http://127.0.0.1:{first_port}" + detail["subscription_path"]).status_code == 200
        assert remote.get(f"http://127.0.0.1:{first_port}/api/subscriptions").status_code == 404
        moved = client.put("/api/network", headers=HEADERS, json={"enabled": True, "port": second_port, "selected_host": "192.168.50.11"}).json()
        assert moved["running"] and moved["selected_host"] == "192.168.50.11"
        with pytest.raises(httpx.ConnectError):
            remote.get(f"http://127.0.0.1:{first_port}" + detail["subscription_path"])
        assert remote.get(f"http://127.0.0.1:{second_port}" + detail["subscription_path"]).status_code == 200
        disabled = client.put("/api/network", headers=HEADERS, json={"enabled": False, "port": second_port, "selected_host": LOCAL_IP}).json()
        assert not disabled["running"] and not disabled["base_url"]
        with pytest.raises(httpx.ConnectError):
            remote.get(f"http://127.0.0.1:{second_port}" + detail["subscription_path"])
    assert client.get(detail["subscription_path"]).status_code == 200
    assert not json.loads((directory / "network.json").read_text())["enabled"]


def test_occupied_port_keeps_existing_listener_and_settings(fixture):
    _, client, detail, directory = fixture
    port = free_port()
    client.put("/api/network", headers=HEADERS, json={"enabled": True, "port": port, "selected_host": LOCAL_IP})
    before = (directory / "network.json").read_text()
    with socket.socket() as occupied:
        occupied.bind(("0.0.0.0", 0))
        occupied.listen(1)
        result = client.put("/api/network", headers=HEADERS, json={"enabled": True, "port": occupied.getsockname()[1], "selected_host": LOCAL_IP})
        assert result.status_code == 400
    assert (directory / "network.json").read_text() == before
    assert client.get("/api/network").json()["port"] == port
    assert httpx.get(f"http://127.0.0.1:{port}" + detail["subscription_path"], trust_env=False).status_code == 200


def test_settings_persist_and_restart_listener(tmp_path, monkeypatch):
    monkeypatch.setattr(lan, "lan_addresses", lambda: [{"address": LOCAL_IP, "preferred": True}])
    port = free_port()
    with TestClient(create_app(tmp_path)) as client:
        result = client.put("/api/network", headers=HEADERS, json={"enabled": True, "port": port, "selected_host": LOCAL_IP})
        assert result.status_code == 200
    with TestClient(create_app(tmp_path)) as reopened:
        status = reopened.get("/api/network").json()
        assert status["running"] and status["port"] == port
        assert httpx.get(f"http://127.0.0.1:{port}/api/network", trust_env=False).status_code == 404


def test_settings_reject_bad_addresses_management_port_and_untrusted_writes(fixture):
    _, client, _, _ = fixture
    assert client.put("/api/network", json={}).status_code == 403
    assert client.put("/api/network", headers={**HEADERS, "Origin": "http://evil.example"}, json={}).status_code == 403
    for address in ("8.8.8.8", "evil.example", "127.0.0.1"):
        assert client.put("/api/network", headers=HEADERS, json={"enabled": True, "port": 8767, "selected_host": address}).status_code == 422
    assert client.put("/api/network", headers=HEADERS, json={"enabled": True, "port": 8767, "selected_host": "10.99.99.99"}).status_code == 400
    with TestClient(client.app, base_url="http://127.0.0.1:8765") as actual:
        assert actual.put("/api/network", headers=HEADERS, json={"enabled": True, "port": 8765, "selected_host": LOCAL_IP}).status_code == 400
