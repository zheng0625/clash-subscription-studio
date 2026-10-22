from pathlib import Path

import pytest

from app.engine import compile_config, empty_edits, parse_config

DEMO = (Path(__file__).resolve().parents[1] / "examples" / "demo.yaml").read_text(encoding="utf-8")


def test_roundtrip_preserves_other_fields_and_secrets():
    text = DEMO + "\ntun:\n  enable: true\n  stack: mixed\ncustom-option: unchanged\n"
    result = compile_config(text, empty_edits())
    assert not result["errors"]
    original = parse_config(text)
    for field in ("dns", "tun", "custom-option", "proxies"):
        assert result["config"][field] == original[field]
    assert "# 演示配置" in result["yaml"]


def test_rename_rewrites_group_rule_and_dialer_references():
    text = DEMO.replace("    cipher: aes-128-gcm", "    dialer-proxy: 节点选择\n    cipher: aes-128-gcm")
    edits = empty_edits()
    edits["proxy_renames"] = {"香港 01": "HK Main"}
    edits["group_overrides"] = {"节点选择": {"name": "主代理"}}
    result = compile_config(text, edits)
    assert not result["errors"]
    assert result["config"]["proxies"][0]["name"] == "HK Main"
    assert result["config"]["proxies"][0]["dialer-proxy"] == "主代理"
    assert "HK Main" in result["config"]["proxy-groups"][0]["proxies"]
    assert result["config"]["rules"][-1] == "MATCH,主代理"


def test_exclusion_removes_group_members_but_rejects_dangling_rule():
    edits = empty_edits()
    edits["excluded_proxies"] = ["香港 01"]
    result = compile_config(DEMO, edits)
    assert not result["errors"]
    assert all("香港 01" not in g["proxies"] for g in result["config"]["proxy-groups"])
    edits["added_rules"] = ["DOMAIN,test.example,美国节点"]
    assert any("不存在的目标" in e for e in compile_config(DEMO, edits)["errors"])


def test_refresh_new_nodes_and_rules_keeps_customizations():
    edits = empty_edits()
    edits["proxy_renames"] = {"香港 01": "HK Main"}
    edits["added_rules"] = ["DOMAIN-SUFFIX,openai.com,节点选择"]
    edits["rule_order"] = edits["added_rules"] + list(parse_config(DEMO)["rules"])
    updated = DEMO.replace("  - MATCH,节点选择", "  - DOMAIN-SUFFIX,new.example,DIRECT\n  - MATCH,节点选择")
    result = compile_config(updated, edits)
    assert not result["errors"]
    assert result["config"]["rules"][0] == edits["added_rules"][0]
    assert result["config"]["rules"][-2:] == ["DOMAIN-SUFFIX,new.example,DIRECT", "MATCH,节点选择"]
    assert result["config"]["proxies"][0]["name"] == "HK Main"


def test_missing_modified_group_is_conflict():
    edits = empty_edits()
    edits["group_overrides"] = {"已消失的组": {"name": "New"}}
    assert any("已从源订阅消失" in e for e in compile_config(DEMO, edits)["errors"])


def test_cycles_duplicate_names_and_empty_groups_are_errors():
    edits = empty_edits()
    edits["new_groups"] = [{"name": "A", "type": "select", "proxies": ["B"]}, {"name": "B", "type": "select", "proxies": ["A"]}]
    assert any("循环引用" in e for e in compile_config(DEMO, edits)["errors"])
    edits["new_groups"] = [{"name": "DIRECT", "type": "select", "proxies": []}]
    errors = compile_config(DEMO, edits)["errors"]
    assert any("内置名称" in e for e in errors)
    assert any("没有可用成员" in e for e in errors)


def test_provider_and_logical_rule_preservation():
    text = """proxy-providers:
  airport:
    type: http
    url: https://example.com/proxies
    path: ./providers/airport.yaml
proxy-groups:
  - name: Proxy
    type: select
    use: [airport]
rule-providers:
  ads:
    type: http
    behavior: domain
    path: ./rules/ads.yaml
    url: https://example.com/rules
rules:
  - AND,((NETWORK,UDP),(DST-PORT,443)),REJECT
  - RULE-SET,ads,Proxy
  - MATCH,Proxy
"""
    edits = empty_edits()
    edits["group_overrides"] = {"Proxy": {"name": "出口"}}
    result = compile_config(text, edits)
    assert not result["errors"]
    assert result["config"]["rules"][0] == "AND,((NETWORK,UDP),(DST-PORT,443)),REJECT"
    assert result["config"]["rules"][1] == "RULE-SET,ads,出口"
    assert result["config"]["proxy-providers"] == parse_config(text)["proxy-providers"]
    assert result["warnings"]


def test_large_group_reference_graph_and_yaml_merge_keys():
    entries = "\n".join(f"  - {{name: G{i}, type: select, proxies: [G{i+1}]}}" for i in range(1100))
    text = "proxies: []\nproxy-groups:\n" + entries + "\n  - {name: G1100, type: select, proxies: [DIRECT]}\nrules: [MATCH,G0]\n"
    # Use one scalar rule, not two YAML list members.
    text = text.replace("rules: [MATCH,G0]", 'rules: ["MATCH,G0"]')
    assert not compile_config(text, empty_edits())["errors"]
    merged = """defaults: &defaults
  type: select
  proxies: [DIRECT, REJECT]
proxy-groups:
  - <<: *defaults
    name: A
  - <<: *defaults
    name: B
rules: ["MATCH,A"]
"""
    edits = empty_edits()
    edits["group_overrides"] = {"A": {"proxies": ["DIRECT"]}}
    config = compile_config(merged, edits)["config"]
    assert config["proxy-groups"][0]["proxies"] == ["DIRECT"]
    assert config["proxy-groups"][1]["proxies"] == ["DIRECT", "REJECT"]


def test_duplicate_renames_and_malformed_logical_rules_are_rejected():
    edits = empty_edits()
    edits["proxy_renames"] = {"香港 01": "日本 01"}
    assert any("重复" in e for e in compile_config(DEMO, edits)["errors"])
    edits = empty_edits()
    edits["added_rules"] = ["AND,((NETWORK,UDP),REJECT"]
    assert any("格式无效" in e for e in compile_config(DEMO, edits)["errors"])


@pytest.mark.parametrize("text", [
    "not a config", "proxies: []\nproxies: []", "proxies: {}", "proxies: [hello]",
    "proxy-groups: [{name: A, type: select, proxies: [{bad: object}]}]",
    "proxies: []\nrules: [123]", "proxies: []\ncycle: &cycle [*cycle]",
    "proxies: []\ncustom: !unknown something",
])
def test_invalid_yaml_rejected_cleanly(text):
    with pytest.raises(ValueError):
        parse_config(text)
