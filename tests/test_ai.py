import copy

import pytest
from fastapi.testclient import TestClient

from app.ai_preset import create_ai_draft
from app.ai_rules import AI_GROUP_NAME, SERVICES, catalogue, managed_rules
from app.engine import compile_config, empty_edits, parse_config
from app.main import create_app
from test_engine import DEMO

HEADERS = {"X-Clash-Studio": "1"}


def test_catalogue_is_explicit_and_excludes_chinese_and_shared_parent_domains():
    data = catalogue()
    assert data["service_count"] == 24
    entries = [(r["type"], r["domain"]) for s in data["services"] for r in s["rules"]]
    assert len(entries) == len(set(entries)) == data["rule_count"]
    assert ("DOMAIN-SUFFIX", "muse.ai") in entries
    assert ("DOMAIN", "generativelanguage.googleapis.com") in entries
    assert ("DOMAIN", "copilot-proxy.githubusercontent.com") in entries
    domains = {domain for _, domain in entries}
    assert not domains & {"google.com", "microsoft.com", "github.com", "cloudflare.com", "stripe.com", "auth0.com", "sentry.io"}
    assert not domains & {"deepseek.com", "kimi.com", "kimi.ai", "moonshot.ai", "qwen.ai", "doubao.com", "minimax.io", "bigmodel.cn"}


def test_ai_draft_is_pure_idempotent_and_keeps_other_edits():
    edits = empty_edits()
    edits["proxy_renames"]["香港 01"] = "我的节点"
    before = copy.deepcopy(edits)
    draft = create_ai_draft(DEMO, edits, "香港 01")
    assert edits == before
    assert not draft["preview"]["errors"]
    assert draft["edits"]["proxy_renames"] == before["proxy_renames"]
    assert draft["preview"]["config"]["proxy-groups"][-1]["proxies"] == ["我的节点"]
    assert draft["preview"]["config"]["rules"][:catalogue()["rule_count"]] == managed_rules(AI_GROUP_NAME)
    repeated = create_ai_draft(DEMO, draft["edits"], "香港 01")
    assert repeated["edits"] == draft["edits"]
    assert repeated["preview"]["config"] == draft["preview"]["config"]


def test_refresh_absorbs_ai_conflicts_and_keeps_other_order():
    draft = create_ai_draft(DEMO, empty_edits(), "节点选择")
    source = DEMO.replace("  - MATCH,节点选择", "  - DOMAIN,api.openai.com,DIRECT\n  - DOMAIN-SUFFIX,claude.ai,流媒体\n  - DOMAIN-SUFFIX,google.com,DIRECT\n  - DOMAIN-SUFFIX,deepseek.com,DIRECT\n  - MATCH,节点选择")
    result = compile_config(source, draft["edits"])
    assert not result["errors"]
    assert result["ai_routing"]["overridden"] == 2
    assert "DOMAIN,api.openai.com,DIRECT" not in result["config"]["rules"]
    assert "DOMAIN-SUFFIX,claude.ai,流媒体" not in result["config"]["rules"]
    count = catalogue()["rule_count"]
    expected = [r for r in parse_config(source)["rules"] if r not in ("DOMAIN,api.openai.com,DIRECT", "DOMAIN-SUFFIX,claude.ai,流媒体")]
    assert result["config"]["rules"][count:] == expected
    assert result["config"]["rules"].index("DOMAIN-SUFFIX,google.com,DIRECT") >= count
    disabled = copy.deepcopy(draft["edits"])
    disabled["ai_routing"] = None
    restored = compile_config(source, disabled)
    assert restored["config"]["rules"] == list(parse_config(source)["rules"])
    assert restored["config"]["proxy-groups"][-1]["name"] == AI_GROUP_NAME


def test_reuses_existing_group_and_resets_auto_membership():
    source = DEMO + f"\n"
    config = parse_config(source)
    config["proxy-groups"].append({"name": AI_GROUP_NAME, "type": "select", "include-all": True, "proxies": ["DIRECT"], "filter": "HK"})
    from app.engine import dump_config
    source = dump_config(config)
    draft = create_ai_draft(source, empty_edits(), "日本 01")
    groups = draft["preview"]["config"]["proxy-groups"]
    assert len([g for g in groups if g["name"] == AI_GROUP_NAME]) == 1
    ai = groups[-1]
    assert ai["proxies"] == ["日本 01"] and not ai["include-all"] and ai["filter"] == ""
    assert not draft["edits"]["new_groups"]


@pytest.mark.parametrize("outlet", ["DIRECT", "REJECT", "不存在的节点"])
def test_rejects_invalid_outlet(outlet):
    with pytest.raises(ValueError):
        create_ai_draft(DEMO, empty_edits(), outlet)


def test_renamed_ai_group_and_missing_group_are_checked():
    draft = create_ai_draft(DEMO, empty_edits(), "日本 01")
    renamed = copy.deepcopy(draft["edits"])
    renamed["new_groups"][0]["name"] = "AI 专线"
    renamed["ai_routing"]["group"] = "AI 专线"
    result = compile_config(DEMO, renamed)
    assert not result["errors"]
    assert "DOMAIN-SUFFIX,muse.ai,AI 专线" in result["config"]["rules"]
    renamed["ai_routing"]["enabled"] = False
    assert compile_config(DEMO, renamed)["config"]["rules"] == list(parse_config(DEMO)["rules"])
    enabled_again = create_ai_draft(DEMO, renamed, "香港 01")
    assert len(enabled_again["edits"]["new_groups"]) == 1
    assert enabled_again["edits"]["ai_routing"] == {"group": "AI 专线", "enabled": True}
    renamed["ai_routing"]["enabled"] = True
    renamed["new_groups"] = []
    assert any("AI 分流的代理组已不存在" in e for e in compile_config(DEMO, renamed)["errors"])


def test_api_draft_publish_refresh_disable_history_and_revision(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        original = client.post("/api/subscriptions", headers=HEADERS, json={"title": "AI 测试", "source_type": "file", "yaml": DEMO}).json()
        base = f"/api/subscriptions/{original['id']}"
        catalogue_response = client.get("/api/presets/ai").json()
        assert catalogue_response["rule_count"] == catalogue()["rule_count"]
        request = {"revision": original["revision"], "edits": original["edits"], "outlet": "日本 01"}
        response = client.post(base + "/ai-preset", headers=HEADERS, json=request)
        assert response.status_code == 200, response.text
        draft = response.json()
        assert client.get(base).json()["revision"] == original["revision"]
        assert "muse.ai" not in client.get(original["subscription_path"]).text
        saved = client.put(base + "/edits", headers=HEADERS, json={"revision": original["revision"], "edits": draft["edits"]}).json()
        assert "DOMAIN-SUFFIX,muse.ai,🤖 AI 服务" in client.get(original["subscription_path"]).text
        assert client.post(base + "/ai-preset", headers=HEADERS, json=request).status_code == 409
        source = DEMO.replace("  - MATCH,节点选择", "  - DOMAIN,api.openai.com,DIRECT\n  - MATCH,节点选择")
        refreshed = client.post(base + "/refresh", headers=HEADERS, json={"revision": saved["revision"], "yaml": source}).json()
        assert refreshed["preview"]["ai_routing"]["overridden"] == 1
        assert "DOMAIN,api.openai.com,DIRECT" not in client.get(original["subscription_path"]).text
        refreshed["edits"]["ai_routing"] = None
        disabled = client.put(base + "/edits", headers=HEADERS, json={"revision": refreshed["revision"], "edits": refreshed["edits"]}).json()
        assert "DOMAIN,api.openai.com,DIRECT" in client.get(original["subscription_path"]).text
        versions = client.get(base + "/history").json()
        restored = client.post(base + f"/history/{versions[1]['id']}/restore", headers=HEADERS, json={"revision": disabled["revision"]}).json()
        assert restored["edits"]["ai_routing"]
        assert "DOMAIN-SUFFIX,muse.ai,🤖 AI 服务" in client.get(original["subscription_path"]).text


def test_self_reference_and_transitive_cycle_are_not_published(tmp_path):
    draft = create_ai_draft(DEMO, empty_edits(), "日本 01")
    with pytest.raises(ValueError, match="不能选择自己"):
        create_ai_draft(DEMO, draft["edits"], AI_GROUP_NAME)
    draft["edits"]["group_overrides"]["节点选择"] = {"proxies": [AI_GROUP_NAME]}
    result = create_ai_draft(DEMO, draft["edits"], "节点选择")
    assert any("循环引用" in e for e in result["preview"]["errors"])
