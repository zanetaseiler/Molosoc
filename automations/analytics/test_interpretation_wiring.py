#!/usr/bin/env python3
"""
Offline tests for the live-caller wiring: role configuration, response
handling, persistence location, and the CLI's refusal paths.

No network, no credentials, no SDK. The Anthropic client is a stub, so every
assertion here is about *our* behaviour when the API answers in a particular
way — including the two ways it answers that are not an error but are also not
a usable result.
"""

import json

import pytest

import intelligence_store as istore
import interpretation_caller as caller_mod
import interpretation_contracts as ic
import interpretation_graph as ig
import report_store as rs
import run_interpretation as run_mod
from interpretation_caller import AnthropicCaller, CallerError
from storage import InMemoryStore


class Block:
    def __init__(self, type_, text=None):
        self.type = type_
        self.text = text


class Usage:
    def __init__(self, i=100, o=50):
        self.input_tokens = i
        self.output_tokens = o
        self.cache_read_input_tokens = 0
        self.cache_creation_input_tokens = 0


class Response:
    def __init__(self, payload=None, stop_reason="end_turn", blocks=None,
                 usage=None):
        self.content = blocks if blocks is not None else [
            Block("text", json.dumps(payload or {}))]
        self.stop_reason = stop_reason
        self.stop_details = None
        self.usage = usage or Usage()


class StubClient:
    """Records every request and returns whatever it was scripted to."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []
        self.messages = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self._responses.pop(0)


# --------------------------------------------------------------------------
# Role configuration — the approved caps, exactly
# --------------------------------------------------------------------------

def test_the_role_configuration_is_what_was_approved():
    config = caller_mod.role_config(env={})
    assert config["specialist"] == {"model": "claude-sonnet-5",
                                    "effort": "medium", "max_tokens": 8000}
    assert config["verifier"] == {"model": "claude-opus-5",
                                  "effort": "high", "max_tokens": 4000}
    assert config["synthesis"] == {"model": "claude-opus-5",
                                   "effort": "high", "max_tokens": 8000}


def test_the_verifier_runs_a_different_model_from_the_specialists():
    """A verifier sharing the specialist's blind spots is not a second opinion."""
    config = caller_mod.role_config(env={})
    assert config["verifier"]["model"] != config["specialist"]["model"]


def test_only_the_specialist_row_can_be_overridden_from_the_environment():
    config = caller_mod.role_config(env={
        "INTERPRETATION_MODEL": "claude-haiku-4-5",
        "INTERPRETATION_EFFORT_SPECIALIST": "low",
    })
    assert config["specialist"]["model"] == "claude-haiku-4-5"
    assert config["specialist"]["effort"] == "low"
    # The independence and gate-honouring guarantees are not settings.
    assert config["verifier"]["model"] == "claude-opus-5"
    assert config["synthesis"]["model"] == "claude-opus-5"


def test_a_bad_effort_level_is_refused_rather_than_sent():
    with pytest.raises(CallerError, match="effort level"):
        caller_mod.role_config(env={"INTERPRETATION_EFFORT_SPECIALIST": "turbo"})


def test_every_node_maps_to_a_role_and_a_schema():
    for node in ig.SPECIALISTS:
        assert caller_mod.ROLE_OF_NODE[node] == caller_mod.ROLE_SPECIALIST
        assert caller_mod.schema_for(node, {})["properties"]["node"]["enum"] == [node]
    assert caller_mod.ROLE_OF_NODE[ig.NODE_VERIFIER] == caller_mod.ROLE_VERIFIER
    assert caller_mod.ROLE_OF_NODE[ig.NODE_SYNTHESIS] == caller_mod.ROLE_SYNTHESIS
    verdict = caller_mod.schema_for(ig.NODE_VERIFIER, {"finding": {"id": "t1"}})
    assert verdict["properties"]["finding_id"]["enum"] == ["t1"]


# --------------------------------------------------------------------------
# The request we actually send
# --------------------------------------------------------------------------

def test_the_request_carries_the_prompt_schema_effort_and_ceiling():
    payload = {"node": "traffic", "findings": [], "unable_to_assess": []}
    client = StubClient([Response(payload)])
    caller = AnthropicCaller(client=client, env={})

    result = caller("traffic", {"facts": [], "fact_ids": []})
    assert result == payload

    sent = client.requests[0]
    assert sent["model"] == "claude-sonnet-5"
    assert sent["max_tokens"] == 8000
    assert sent["output_config"]["effort"] == "medium"
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert sent["output_config"]["format"]["schema"]["properties"]["node"]["enum"] \
        == ["traffic"]
    assert "evidence_fact_ids" in sent["system"]


def test_the_payload_is_found_past_a_thinking_block():
    """Thinking is on by default; content[0] is often not the answer."""
    payload = {"node": "seo", "findings": [], "unable_to_assess": []}
    client = StubClient([Response(blocks=[
        Block("thinking", None), Block("text", json.dumps(payload))])])
    assert AnthropicCaller(client=client, env={})("seo", {}) == payload


def test_a_refusal_is_reported_as_a_refusal():
    client = StubClient([Response({}, stop_reason="refusal")])
    with pytest.raises(CallerError, match="declined"):
        AnthropicCaller(client=client, env={})("traffic", {})


def test_truncation_at_the_ceiling_says_so_instead_of_looking_like_bad_json():
    client = StubClient([Response({}, stop_reason="max_tokens")])
    with pytest.raises(CallerError, match="ceiling"):
        AnthropicCaller(client=client, env={})("synthesis", {})


def test_unparseable_output_is_reported_as_such():
    client = StubClient([Response(blocks=[Block("text", "not json")])])
    with pytest.raises(CallerError, match="not valid JSON"):
        AnthropicCaller(client=client, env={})("traffic", {})


# --------------------------------------------------------------------------
# Usage recording
# --------------------------------------------------------------------------

def test_usage_is_recorded_per_call_and_rolled_up_by_role():
    payload = {"node": "traffic", "findings": [], "unable_to_assess": []}
    client = StubClient([
        Response(payload, usage=Usage(1000, 200)),
        Response({"finding_id": "t1", "verdict": ic.VERDICT_CONFIRMED,
                  "reason": "checked", "confidence": "medium"},
                 usage=Usage(500, 100)),
    ])
    caller = AnthropicCaller(client=client, env={})
    caller("traffic", {})
    caller(ig.NODE_VERIFIER, {"finding": {"id": "t1"}})

    usage = caller.usage_summary()
    assert usage["attempts"] == 2
    assert usage["input_tokens"] == 1500
    assert usage["output_tokens"] == 300
    assert usage["by_role"]["specialist"]["model"] == "claude-sonnet-5"
    assert usage["by_role"]["verifier"]["model"] == "claude-opus-5"
    assert usage["by_role"]["specialist"]["attempts"] == 1
    assert usage["truncated_calls"] == []
    assert len(usage["per_call"]) == 2


def test_usage_reaches_the_handoff_provenance():
    import marketing_intelligence as mi
    import test_interpretation as t

    doc = t.document()
    result = ig.run_graph(doc, t.scripted(t.FULL_FINDINGS))
    result["manifest"]["usage"] = {"attempts": 11, "input_tokens": 9000,
                                   "output_tokens": 1200, "by_role": {}}
    handoff = mi.build(doc, result)
    assert handoff["provenance"]["token_usage"]["attempts"] == 11
    assert handoff["provenance"]["token_usage"]["input_tokens"] == 9000


# --------------------------------------------------------------------------
# Where the document is stored
# --------------------------------------------------------------------------

def test_the_key_is_derived_from_the_report_directory():
    key = istore.key_for("2026-08-13")
    assert key == "reports/weekly/data/2026/08/2026-08-13/marketing_intelligence.json"
    # Derived, not composed separately — the two must not be able to drift.
    assert key == f"{rs.report_dir('2026-08-13')}/{istore.FILENAME}"


def test_a_consumer_finds_it_by_swapping_the_filename_on_the_report_key():
    """This is why no second mutable pointer had to be created."""
    report_key = rs.report_key("2026-08-13", "json")
    assert istore.key_for_report_key(report_key) == istore.key_for("2026-08-13")


def test_it_sits_under_the_prefix_the_retention_rule_already_covers():
    assert istore.key_for("2026-08-13").startswith(rs.DATA_ROOT + "/")
    # And it is not one of the two objects the delete grant covers, so
    # publishing it needs no IAM change.
    assert istore.key_for("2026-08-13") not in rs.MUTABLE_KEYS


def test_publishing_twice_is_refused_and_leaves_the_first_alone():
    store = InMemoryStore()
    istore.publish(store, {"schema_version": "1.0.0", "n": 1}, "2026-08-13")
    with pytest.raises(istore.AlreadyPublished):
        istore.publish(store, {"schema_version": "1.0.0", "n": 2}, "2026-08-13")
    kept = json.loads(store.get_text(istore.key_for("2026-08-13")))
    assert kept["n"] == 1


# --------------------------------------------------------------------------
# CLI refusal paths
# --------------------------------------------------------------------------

def test_the_kill_switch_stops_the_run_before_anything_is_read(monkeypatch):
    monkeypatch.setenv("INTERPRETATION_ENABLED", "false")
    assert run_mod.main(["--report-date", "2026-08-13"]) == 4


def test_the_kill_switch_defaults_to_on():
    assert run_mod.enabled(env={}) is True
    assert run_mod.enabled(env={"INTERPRETATION_ENABLED": "false"}) is False
    assert run_mod.enabled(env={"INTERPRETATION_ENABLED": "0"}) is False


def test_a_missing_report_is_reported_rather_than_interpreted(monkeypatch, tmp_path):
    monkeypatch.delenv("ANALYTICS_BUCKET", raising=False)
    assert run_mod.main([
        "--report-date", "2026-08-13", "--store-root", str(tmp_path)]) == 1


def test_the_dry_run_makes_no_model_call(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("ANALYTICS_BUCKET", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-used-in-a-dry-run")
    store = run_mod.LocalFileStore(str(tmp_path))
    store.put_text(rs.report_key("2026-08-13", "json"),
                   json.dumps({"report_date": "2026-08-13", "facts": [],
                               "readiness": "ready"}))

    assert run_mod.main(["--report-date", "2026-08-13",
                         "--store-root", str(tmp_path), "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "no model call was made" in out
    assert "claude-sonnet-5" in out and "claude-opus-5" in out


def test_an_already_published_week_is_refused_before_any_call(monkeypatch, tmp_path):
    monkeypatch.delenv("ANALYTICS_BUCKET", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "never-used")
    store = run_mod.LocalFileStore(str(tmp_path))
    store.put_text(rs.report_key("2026-08-13", "json"),
                   json.dumps({"report_date": "2026-08-13", "facts": [],
                               "readiness": "ready"}))
    store.put_text(istore.key_for("2026-08-13"), "{}")

    assert run_mod.main(["--report-date", "2026-08-13", "--persist",
                         "--store-root", str(tmp_path)]) == 3


# --------------------------------------------------------------------------
# Boundary
# --------------------------------------------------------------------------

def test_only_one_vendor_is_referenced():
    import pathlib
    source = pathlib.Path(__file__).with_name("interpretation_caller.py") \
        .read_text(encoding="utf-8")
    for other in ("openai", "OpenAI", "gemini", "vertexai", "bedrock"):
        assert other not in source


def test_no_module_below_the_graph_imports_the_caller():
    """The layer boundary runs one way only."""
    import pathlib
    here = pathlib.Path(__file__).parent
    for module in ("analysis.py", "report_store.py", "weekly_report.py",
                   "dashboard.py", "thresholds.py"):
        source = (here / module).read_text(encoding="utf-8")
        assert "interpretation_caller" not in source, module
        assert "anthropic" not in source.lower(), module
