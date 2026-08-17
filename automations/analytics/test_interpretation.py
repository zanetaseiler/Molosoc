#!/usr/bin/env python3
"""
Offline fixture tests for the interpretation graph.

No network, no credentials, no storage, no model. Every "call" is a scripted
caller so each scenario is exactly reproducible — which is the only way the
budget and completeness guarantees can be asserted rather than hoped for.
"""

import copy

import pytest

import interpretation_contracts as ic
import interpretation_graph as ig
import marketing_intelligence as mi
from analysis_model import HIGH, INSUFFICIENT_DATA, LOW, MEDIUM, READY
from records import CLARITY, GA4, GSC


# --------------------------------------------------------------------------
# Fixtures — hand-built documents so every scenario is exact
# --------------------------------------------------------------------------

def fact(fid, source, metric, period_value, comparison_value=None,
         delta_pct=None, significant=True, meets_minimum=True):
    return {
        "id": fid, "source": source, "entity_type": "site", "entity_id": "site",
        "metric": metric, "period_value": period_value,
        "comparison_value": comparison_value,
        "delta_abs": (None if comparison_value is None
                      else period_value - comparison_value),
        "delta_pct": delta_pct, "sample_size": period_value,
        "meets_minimum": meets_minimum, "significant": significant,
        "notes": {},
    }


def document(sources=(GA4, GSC, CLARITY), readiness=READY):
    facts = []
    if GA4 in sources:
        facts += [
            fact("f_ga4_sessions", GA4, "ga4_sessions", 820, 1000, -0.18),
            fact("f_ga4_purchases", GA4, "ga4_purchases", 12, 20, -0.40),
        ]
    if GSC in sources:
        facts += [fact("f_gsc_clicks", GSC, "gsc_clicks", 300, 250, 0.20)]
    if CLARITY in sources:
        facts += [fact("f_clarity_rage", CLARITY, "clarity_rage_click_rate",
                       0.09, 0.04, 1.25)]
    return {
        "schema_version": "1.0.0",
        "kind": "molosoc.weekly_marketing_analysis",
        "report_date": "2026-08-13",
        "period": {"start": "2026-08-07", "end": "2026-08-13"},
        "comparison_period": {"start": "2026-07-31", "end": "2026-08-06"},
        "readiness": readiness,
        "readiness_note": ("below the volume floor" if readiness != READY else ""),
        "facts": facts,
        "data_quality": {"conversions": {"state": "ok"}},
        "conversions": {"state": "ok"},
        "ecommerce_tracking_boundary": {"state": "active"},
        "tracking_coverage": {"state": "aligned"},
        "source_coverage": {"clarity_ledger": {"days_available": 14}},
        "storage": {"json_key": "reports/weekly/data/2026/08/2026-08-13/report.json"},
    }


def finding(fid, node, kind, statement, evidence, severity=ic.SEV_MEDIUM,
            confidence=MEDIUM, alternatives=("seasonality",)):
    out = {"id": fid, "kind": kind, "statement": statement,
           "evidence_fact_ids": list(evidence), "severity": severity,
           "confidence": confidence}
    if kind == ic.JUDGMENT:
        out["alternative_explanations"] = list(alternatives)
    return out


def scripted(specialist_findings=None, verdict=ic.VERDICT_CONFIRMED,
             themes=None, malformed_nodes=(), fail_forever=()):
    """A caller whose every response is decided in advance.

    `malformed_nodes` return junk on the first attempt and valid output on the
    retry; `fail_forever` never recovers, which is how the retry cap gets
    exercised in both directions.
    """
    specialist_findings = specialist_findings or {}
    seen = {}

    def caller(node, request):
        seen[node] = seen.get(node, 0) + 1
        first = seen[node] == 1

        if node in ig.SPECIALISTS:
            if node in fail_forever or (node in malformed_nodes and first):
                return {"node": node, "findings": "not-a-list"}
            return {"node": node, "findings": specialist_findings.get(node, []),
                    "unable_to_assess": []}

        if node == ig.NODE_VERIFIER:
            fid = request["finding"]["id"]
            chosen = verdict(fid) if callable(verdict) else verdict
            return {"finding_id": fid, "verdict": chosen,
                    "reason": f"independent check of {fid}", "confidence": MEDIUM}

        if node == ig.NODE_SYNTHESIS:
            if themes is not None:
                return {"themes": themes, "open_questions": []}
            ids = [f["id"] for f in request["findings"]]
            return {"themes": [{"title": "Overall", "narrative": "Movements observed.",
                                "based_on_finding_ids": ids}],
                    "open_questions": ["Is the Clarity window long enough yet?"]}
        raise AssertionError(f"unexpected node {node}")

    caller.seen = seen
    return caller


FULL_FINDINGS = {
    ig.NODE_TRAFFIC: [
        finding("t1", "traffic", ic.OBSERVATION,
                "Sessions moved from 1000 to 820 week over week.",
                ["f_ga4_sessions"]),
        finding("t2", "traffic", ic.JUDGMENT,
                "The session decline looks broad rather than page-specific.",
                ["f_ga4_sessions"], severity=ic.SEV_HIGH, confidence=MEDIUM),
    ],
    ig.NODE_SEO: [
        finding("s1", "seo", ic.JUDGMENT,
                "Search demand held up while site sessions fell.",
                ["f_gsc_clicks"], severity=ic.SEV_MEDIUM, confidence=HIGH),
    ],
    ig.NODE_UX: [
        finding("u1", "ux", ic.JUDGMENT,
                "Rage clicking is elevated relative to the prior week.",
                ["f_clarity_rage"], severity=ic.SEV_HIGH, confidence=LOW),
    ],
    ig.NODE_CONVERSION: [
        finding("c1", "conversion", ic.OBSERVATION,
                "Purchases moved from 20 to 12.", ["f_ga4_purchases"]),
    ],
}


def run(doc, caller, budget=None):
    return ig.run_graph(doc, caller, now=None, budget=budget)


# --------------------------------------------------------------------------
# 1. Complete run
# --------------------------------------------------------------------------

def test_complete_run_covers_every_domain_and_stays_in_budget():
    doc = document()
    caller = scripted(FULL_FINDINGS)
    result = run(doc, caller)
    m = result["manifest"]

    assert m["status"] == ig.RUN_COMPLETE
    assert sorted(m["specialists"]["ran"]) == sorted(ig.SPECIALISTS)
    assert m["specialists"]["skipped_missing_input"] == []
    assert m["sources"]["missing"] == []

    budget = m["budget"]
    assert budget["calls_made"]["specialist"] == 4, "one call per specialist"
    assert budget["calls_made"]["specialist"] <= ig.MAX_SPECIALIST_CALLS
    assert budget["calls_made"]["verifier"] <= ig.MAX_VERIFIER_CALLS
    assert budget["calls_made"]["synthesis"] == 1
    assert budget["retries"] == {}


def test_only_judgments_consume_verifier_calls():
    """Observations are already deterministic; verifying them buys nothing."""
    doc = document()
    caller = scripted(FULL_FINDINGS)
    result = run(doc, caller)

    judgments = sum(1 for fs in FULL_FINDINGS.values()
                    for f in fs if f["kind"] == ic.JUDGMENT)
    assert result["manifest"]["budget"]["calls_made"]["verifier"] == judgments == 3

    observations = [f for f in result["verified_findings"]
                    if f["kind"] == ic.OBSERVATION]
    assert observations, "observations must still reach synthesis"
    assert all(f["verification"]["verdict"] == "not_required" for f in observations)


def test_the_graph_has_no_edges_between_specialists():
    """Each specialist sees only its own slice — that is the whole claim."""
    doc = document()
    slices = ig.slice_inputs(doc)
    assert {f["source"] for f in slices[ig.NODE_TRAFFIC]["facts"]} == {GA4}
    assert {f["source"] for f in slices[ig.NODE_SEO]["facts"]} == {GSC}
    assert {f["source"] for f in slices[ig.NODE_UX]["facts"]} == {CLARITY}
    # A node cannot cite what it was never given.
    with pytest.raises(ic.ContractError, match="not in this node's input slice"):
        ic.validate_specialist(
            {"node": "traffic",
             "findings": [finding("x", "traffic", ic.OBSERVATION,
                                  "Cross-source claim.", ["f_clarity_rage"])]},
            "traffic", set(slices[ig.NODE_TRAFFIC]["fact_ids"]), {})


# --------------------------------------------------------------------------
# 2. Missing Clarity
# --------------------------------------------------------------------------

def test_missing_clarity_skips_ux_and_marks_the_run_partial():
    doc = document(sources=(GA4, GSC))
    caller = scripted({k: v for k, v in FULL_FINDINGS.items() if k != ig.NODE_UX})
    result = run(doc, caller)
    m = result["manifest"]

    assert m["status"] == ig.RUN_PARTIAL
    assert m["specialists"]["skipped_missing_input"] == [ig.NODE_UX]
    assert m["sources"]["missing"] == [CLARITY]
    assert ig.NODE_UX not in caller.seen, "a skipped node must not be called"

    detail = m["specialists"]["detail"][ig.NODE_UX]
    assert detail["status"] == ic.STATUS_SKIPPED_NO_INPUT
    assert detail["missing_sources"] == [CLARITY]
    assert "not called" in detail["reason"]

    doc_out = mi.build(doc, result)
    uncovered = {d["domain"] for d in doc_out["completeness"]["uncovered_domains"]}
    assert uncovered == {"experience"}
    assert not mi.validate(doc_out)


def test_missing_clarity_invents_nothing():
    """A missing source produces absence, never a placeholder or a zero."""
    doc = document(sources=(GA4, GSC))
    handoff = mi.build(doc, run(doc, scripted(FULL_FINDINGS)))

    assert CLARITY not in handoff["completeness"]["sources_available"]
    assert CLARITY in handoff["completeness"]["sources_missing"]

    # No UX finding exists anywhere — not verified, not excluded, not empty-
    # but-present. The caller was ready to supply one; the graph never asked.
    assert all(f["node"] != ig.NODE_UX for f in handoff["verified_findings"])
    assert all(f["node"] != ig.NODE_UX for f in handoff["excluded_findings"])

    # And no Clarity fact is cited by anything that did run.
    for f in handoff["verified_findings"]:
        assert not any(e.startswith("f_clarity") for e in f["evidence_fact_ids"])


# --------------------------------------------------------------------------
# 3. Missing GA4
# --------------------------------------------------------------------------

def test_missing_ga4_skips_both_dependent_specialists():
    """Traffic and conversion both need GA4 — neither may run without it."""
    doc = document(sources=(GSC, CLARITY))
    caller = scripted(FULL_FINDINGS)
    result = run(doc, caller)
    m = result["manifest"]

    assert m["status"] == ig.RUN_PARTIAL
    assert sorted(m["specialists"]["skipped_missing_input"]) == [
        ig.NODE_CONVERSION, ig.NODE_TRAFFIC]
    assert sorted(m["specialists"]["ran"]) == [ig.NODE_SEO, ig.NODE_UX]
    assert ig.NODE_TRAFFIC not in caller.seen
    assert ig.NODE_CONVERSION not in caller.seen

    handoff = mi.build(doc, result)
    assert {d["domain"] for d in handoff["completeness"]["uncovered_domains"]} == {
        "acquisition", "conversion"}
    assert handoff["completeness"]["status"] == ig.RUN_PARTIAL
    assert not mi.validate(handoff)


# --------------------------------------------------------------------------
# 4. Low volume / no recommendation
# --------------------------------------------------------------------------

def test_low_volume_readiness_gate_survives_the_handoff():
    doc = document(readiness=INSUFFICIENT_DATA)
    result = run(doc, scripted(FULL_FINDINGS))
    handoff = mi.build(doc, result)

    assert handoff["readiness"]["state"] == INSUFFICIENT_DATA
    assert handoff["readiness"]["recommendations_withheld"] is True
    assert handoff["priorities"] == [], "no advice may cross the boundary"
    assert "not be worked around" in handoff["readiness"]["meaning"]
    # Findings still cross — withholding advice is not withholding facts.
    assert handoff["verified_findings"]
    assert not mi.validate(handoff)


def test_a_ready_report_does_produce_priorities():
    """The gate has to be the reason, not a bug that always empties the list."""
    doc = document(readiness=READY)
    result = run(doc, scripted(FULL_FINDINGS))
    handoff = mi.build(doc, result)
    assert handoff["priorities"], "ready reports must still yield priorities"


# --------------------------------------------------------------------------
# 5. Verifier rejection / downgrade
# --------------------------------------------------------------------------

def test_a_rejected_finding_is_excluded_with_its_reason():
    doc = document()
    caller = scripted(FULL_FINDINGS,
                      verdict=lambda fid: (ic.VERDICT_REJECTED if fid == "u1"
                                           else ic.VERDICT_CONFIRMED))
    result = run(doc, caller)

    verified = {f["id"] for f in result["verified_findings"]}
    excluded = {f["id"]: f for f in result["excluded_findings"]}
    assert "u1" not in verified
    assert excluded["u1"]["excluded_because"] == ic.EXCLUDED_REJECTED
    assert excluded["u1"]["verification"]["verdict"] == ic.VERDICT_REJECTED
    assert excluded["u1"]["verification"]["reason"]

    handoff = mi.build(doc, result)
    assert "u1" in {f["id"] for f in handoff["excluded_findings"]}
    assert "u1" not in {f["id"] for f in handoff["verified_findings"]}
    assert not mi.validate(handoff)


def test_a_downgraded_finding_survives_with_lower_confidence():
    doc = document()
    caller = scripted(FULL_FINDINGS,
                      verdict=lambda fid: (ic.VERDICT_DOWNGRADED if fid == "s1"
                                           else ic.VERDICT_CONFIRMED))
    result = run(doc, caller)
    s1 = next(f for f in result["verified_findings"] if f["id"] == "s1")

    assert s1["confidence"] == MEDIUM, "high downgrades one step to medium"
    assert s1["downgraded_from"] == HIGH
    assert s1["verification"]["verdict"] == ic.VERDICT_DOWNGRADED


def test_verifier_budget_is_capped_and_the_overflow_is_declared():
    """Beyond six judgments, the rest are excluded — explicitly, not dropped."""
    many = {ig.NODE_TRAFFIC: [
        finding(f"t{i}", "traffic", ic.JUDGMENT,
                "A judgment about sessions.", ["f_ga4_sessions"],
                severity=ic.SEV_MEDIUM) for i in range(9)]}
    doc = document()
    result = run(doc, scripted(many))

    assert result["manifest"]["budget"]["calls_made"]["verifier"] == ig.MAX_VERIFIER_CALLS
    overflow = [f for f in result["excluded_findings"]
                if f["excluded_because"] == ic.EXCLUDED_UNVERIFIED]
    assert len(overflow) == 3
    assert all(f.get("detail") for f in overflow)


def test_verification_prioritises_high_severity_low_confidence():
    findings = [
        finding("low", "traffic", ic.JUDGMENT, "A.", ["f_ga4_sessions"],
                severity=ic.SEV_LOW, confidence=HIGH),
        finding("worst", "traffic", ic.JUDGMENT, "B.", ["f_ga4_sessions"],
                severity=ic.SEV_HIGH, confidence=LOW),
    ]
    normalized = [dict(f, node="traffic") for f in findings]
    selected, _ = ig.select_for_verification(normalized, limit=1)
    assert selected[0]["id"] == "worst"


# --------------------------------------------------------------------------
# 6. Malformed specialist output
# --------------------------------------------------------------------------

def test_malformed_output_is_retried_once_and_then_succeeds():
    doc = document()
    caller = scripted(FULL_FINDINGS, malformed_nodes=(ig.NODE_SEO,))
    result = run(doc, caller)
    m = result["manifest"]

    assert m["specialists"]["detail"][ig.NODE_SEO]["status"] == ic.STATUS_OK
    assert m["budget"]["retries"] == {ig.NODE_SEO: 1}
    assert m["budget"]["calls_made"]["specialist"] == 4, \
        "a retry must not consume the 4-call specialist cap"
    assert caller.seen[ig.NODE_SEO] == 2


def test_a_node_that_stays_malformed_fails_the_run_partially():
    doc = document()
    caller = scripted(FULL_FINDINGS, fail_forever=(ig.NODE_SEO,))
    result = run(doc, caller)
    m = result["manifest"]

    assert m["specialists"]["failed"] == [ig.NODE_SEO]
    assert m["specialists"]["detail"][ig.NODE_SEO]["status"] == ic.STATUS_FAILED_CONTRACT
    assert m["status"] == ig.RUN_PARTIAL
    assert m["budget"]["retries"][ig.NODE_SEO] == 1
    assert caller.seen[ig.NODE_SEO] == 2, "exactly one retry, never two"
    # No SEO finding was invented to fill the hole.
    assert all(f["node"] != ig.NODE_SEO for f in result["verified_findings"])

    handoff = mi.build(doc, result)
    seo = next(d for d in handoff["completeness"]["uncovered_domains"]
               if d["node"] == ig.NODE_SEO)
    assert seo["status"] == ic.STATUS_FAILED_CONTRACT
    assert seo["reason"]


def test_the_contract_rejects_fabricated_numbers():
    allowed = {"f_ga4_sessions"}
    facts = {"f_ga4_sessions": fact("f_ga4_sessions", GA4, "ga4_sessions",
                                    820, 1000, -0.18)}
    payload = {"node": "traffic", "findings": [
        finding("t1", "traffic", ic.OBSERVATION,
                "Sessions fell to 640 this week.", ["f_ga4_sessions"])]}
    with pytest.raises(ic.ContractError, match="not supported by its cited facts"):
        ic.validate_specialist(payload, "traffic", allowed, facts)

    # The real numbers, including the percentage rendering, are accepted.
    ok = {"node": "traffic", "findings": [
        finding("t1", "traffic", ic.OBSERVATION,
                "Sessions moved from 1000 to 820, a change of 18%.",
                ["f_ga4_sessions"])]}
    assert ic.validate_specialist(ok, "traffic", allowed, facts)["findings"]


def test_the_contract_rejects_causal_language():
    allowed = {"f_ga4_sessions"}
    facts = {"f_ga4_sessions": fact("f_ga4_sessions", GA4, "ga4_sessions", 820, 1000)}
    payload = {"node": "traffic", "findings": [
        finding("t1", "traffic", ic.JUDGMENT,
                "The slower page caused the drop in sessions.", ["f_ga4_sessions"])]}
    with pytest.raises(ic.ContractError, match="causal language"):
        ic.validate_specialist(payload, "traffic", allowed, facts)


def test_a_judgment_without_an_alternative_is_rejected():
    allowed = {"f_ga4_sessions"}
    facts = {"f_ga4_sessions": fact("f_ga4_sessions", GA4, "ga4_sessions", 820, 1000)}
    payload = {"node": "traffic", "findings": [
        {"id": "t1", "kind": ic.JUDGMENT, "statement": "Traffic looks soft.",
         "evidence_fact_ids": ["f_ga4_sessions"], "severity": ic.SEV_LOW,
         "confidence": MEDIUM, "alternative_explanations": []}]}
    with pytest.raises(ic.ContractError, match="alternative explanation"):
        ic.validate_specialist(payload, "traffic", allowed, facts)


# --------------------------------------------------------------------------
# 7. Partial-run synthesis
# --------------------------------------------------------------------------

def test_synthesis_runs_on_a_partial_graph_and_says_so():
    doc = document(sources=(GA4, GSC))
    result = run(doc, scripted(FULL_FINDINGS))

    assert result["manifest"]["synthesis"]["status"] == ic.STATUS_OK
    assert result["manifest"]["status"] == ig.RUN_PARTIAL
    handoff = mi.build(doc, result)
    assert handoff["completeness"]["status"] == ig.RUN_PARTIAL
    assert handoff["themes"]
    assert not mi.validate(handoff)


def test_synthesis_may_not_cite_a_finding_that_failed_verification():
    doc = document()
    caller = scripted(
        FULL_FINDINGS,
        verdict=lambda fid: (ic.VERDICT_REJECTED if fid == "u1"
                             else ic.VERDICT_CONFIRMED),
        themes=[{"title": "Bad", "narrative": "Leaning on a rejected finding.",
                 "based_on_finding_ids": ["u1"]}])
    result = run(doc, caller)
    assert result["synthesis"] is None
    assert result["manifest"]["synthesis"]["status"] == ic.STATUS_FAILED_CONTRACT
    assert "did not survive verification" in result["manifest"]["synthesis"]["error"]


def test_synthesis_is_skipped_when_nothing_survived():
    doc = document()
    caller = scripted(FULL_FINDINGS, verdict=ic.VERDICT_REJECTED)
    # Remove observations so literally nothing survives.
    only_judgments = {k: [f for f in v if f["kind"] == ic.JUDGMENT]
                      for k, v in FULL_FINDINGS.items()}
    caller = scripted(only_judgments, verdict=ic.VERDICT_REJECTED)
    result = run(doc, caller)

    assert result["synthesis"] is None
    assert result["manifest"]["synthesis"]["status"] == ic.STATUS_SKIPPED_NO_INPUT
    assert result["manifest"]["budget"]["calls_made"]["synthesis"] == 0
    handoff = mi.build(doc, result)
    assert handoff["themes"] == []
    assert not mi.validate(handoff)


def test_synthesis_never_receives_raw_facts():
    """The whole point of the node: findings in, no payloads."""
    doc = document()
    captured = {}
    inner = scripted(FULL_FINDINGS)

    def caller(node, request):
        if node == ig.NODE_SYNTHESIS:
            captured["request"] = copy.deepcopy(request)
        return inner(node, request)

    run(doc, caller)
    request = captured["request"]
    assert set(request) == {"findings", "readiness", "recommendations_withheld"}
    for f in request["findings"]:
        assert "evidence_fact_ids" not in f
    blob = str(request)
    assert "period_value" not in blob and "sample_size" not in blob


# --------------------------------------------------------------------------
# 8. Analytics -> Marketing handoff schema
# --------------------------------------------------------------------------

def test_the_handoff_validates_and_carries_its_consumer_contract():
    doc = document()
    handoff = mi.build(doc, run(doc, scripted(FULL_FINDINGS)))

    assert mi.validate(handoff) == []
    assert handoff["schema_version"] == mi.SCHEMA_VERSION
    assert handoff["kind"] == mi.document_kind()
    assert handoff["report_ref"]["json_key"]
    assert handoff["provenance"]["generated_from"].startswith("verified findings only")
    assert handoff["consumer_contract"]["never_reopen_readiness_gate"] is True


def test_the_handoff_validator_catches_a_forged_document():
    doc = document()
    handoff = mi.build(doc, run(doc, scripted(FULL_FINDINGS)))

    forged = copy.deepcopy(handoff)
    forged["completeness"]["status"] = ig.RUN_COMPLETE
    forged["completeness"]["sources_missing"] = [CLARITY]
    assert "status complete while sources are missing" in mi.validate(forged)

    forged = copy.deepcopy(handoff)
    forged["readiness"]["recommendations_withheld"] = True
    assert any("priorities present" in p for p in mi.validate(forged))

    forged = copy.deepcopy(handoff)
    forged["themes"] = [{"title": "X", "narrative": "Y",
                         "based_on_finding_ids": ["nope"]}]
    assert any("cites unverified" in p for p in mi.validate(forged))


def test_every_verified_finding_is_traceable_back_to_facts():
    doc = document()
    handoff = mi.build(doc, run(doc, scripted(FULL_FINDINGS)))
    known = {f["id"] for f in doc["facts"]}
    for f in handoff["verified_findings"]:
        assert f["evidence_fact_ids"]
        assert set(f["evidence_fact_ids"]) <= known
        assert f["verification"]


def test_the_handoff_is_json_serialisable():
    doc = document()
    handoff = mi.build(doc, run(doc, scripted(FULL_FINDINGS)))
    assert ig.to_json(handoff).startswith("{")


# --------------------------------------------------------------------------
# Boundary: this layer must not have touched anything below it
# --------------------------------------------------------------------------

def test_the_graph_never_recomputes_significance_or_thresholds():
    import pathlib
    for module in ("interpretation_graph.py", "interpretation_contracts.py",
                   "marketing_intelligence.py"):
        source = pathlib.Path(__file__).with_name(module).read_text(encoding="utf-8")
        assert "import thresholds" not in source, module
        assert "is_significant" not in source, module
        assert "MIN_" not in source, module


def test_the_graph_makes_no_network_or_storage_calls():
    import pathlib
    for module in ("interpretation_graph.py", "interpretation_contracts.py",
                   "marketing_intelligence.py"):
        source = pathlib.Path(__file__).with_name(module).read_text(encoding="utf-8")
        for forbidden in ("requests", "urllib", "storage_gcs", "google.",
                          "clarity_api", "google_hydrate"):
            assert forbidden not in source, f"{module} references {forbidden}"


def test_budget_caps_are_exactly_what_was_specified():
    assert ig.MAX_SPECIALIST_CALLS == 4
    assert ig.MAX_VERIFIER_CALLS == 6
    assert ig.MAX_SYNTHESIS_CALLS == 1
    assert ig.MAX_RETRIES_PER_NODE == 1
    assert len(ig.SPECIALISTS) == 4


def test_the_budget_refuses_to_go_over():
    budget = ig.CallBudget(specialists=1)
    budget.spend("specialist")
    with pytest.raises(ig.BudgetExceeded):
        budget.spend("specialist")


# --------------------------------------------------------------------------
# Parameterised client slug (item 1)
# --------------------------------------------------------------------------

def test_the_document_kind_is_parameterised_and_defaults_to_molosoc():
    import client_config
    assert client_config.DEFAULT_CLIENT_SLUG == "molosoc"
    assert mi.document_kind(env={}) == "molosoc.marketing_intelligence"
    assert mi.document_kind(env={"CLIENT_SLUG": "acme"}) == "acme.marketing_intelligence"


def test_a_second_client_gets_its_own_kind_end_to_end():
    doc = document()
    handoff = mi.build(doc, run(doc, scripted(FULL_FINDINGS)), client_slug="acme")
    assert handoff["kind"] == "acme.marketing_intelligence"
    assert mi.validate(handoff) == [], "a non-default slug must still validate"


def test_a_malformed_slug_is_refused_rather_than_silently_used():
    import client_config
    for bad in ("Acme", "two words", "-lead", ""):
        env = {"CLIENT_SLUG": bad}
        if bad == "":
            assert client_config.client_slug(env) == "molosoc"  # blank -> default
            continue
        with pytest.raises(client_config.ConfigError):
            client_config.client_slug(env)


def test_the_validator_rejects_a_kind_that_is_not_the_contract():
    doc = document()
    handoff = mi.build(doc, run(doc, scripted(FULL_FINDINGS)))
    forged = copy.deepcopy(handoff)
    forged["kind"] = "molosoc.weekly_marketing_analysis"
    assert any("is not <client_slug>" in p for p in mi.validate(forged))


def test_no_client_name_is_hardcoded_in_the_graph_layer():
    import pathlib
    for module in ("interpretation_graph.py", "interpretation_contracts.py",
                   "marketing_intelligence.py", "interpretation_prompts.py"):
        source = pathlib.Path(__file__).with_name(module).read_text(encoding="utf-8")
        assert "molosoc" not in source.lower(), module


# --------------------------------------------------------------------------
# Specialist prompts (item 2)
# --------------------------------------------------------------------------

def test_every_node_has_a_prompt():
    import interpretation_prompts as ip
    assert set(ip.SPECIALIST_PROMPTS) == set(ig.SPECIALISTS)
    assert set(ip.PROMPTS) == set(ig.SPECIALISTS) | {ig.NODE_VERIFIER, ig.NODE_SYNTHESIS}
    assert all(p.strip() for p in ip.PROMPTS.values())


def test_a_specialist_prompt_never_mentions_a_source_outside_its_slice():
    """The prompt must not offer scope the input slice cannot support."""
    import interpretation_prompts as ip
    foreign = {
        ig.NODE_TRAFFIC: ("search console", "clarity"),
        ig.NODE_SEO: ("clarity", "ga4 purchase"),
        ig.NODE_UX: ("search console", "ga4 sessions"),
    }
    for node, terms in foreign.items():
        body = ip.SPECIALIST_PROMPTS[node].lower()
        for term in terms:
            # Naming a source it cannot see is only allowed as an explicit
            # statement of absence.
            for line in body.splitlines():
                if term in line:
                    assert ("do not have" in line or "cannot" in line
                            or "not have" in line), f"{node}: {line!r}"


def test_the_prompts_state_the_contract_they_are_validated_against():
    import interpretation_prompts as ip
    for node in ig.SPECIALISTS:
        body = ip.SPECIALIST_PROMPTS[node]
        assert "evidence_fact_ids" in body
        assert "alternative_explanations" in body
        assert ic.OBSERVATION in body and ic.JUDGMENT in body
        assert "causal" in body.lower()
        assert '"node": "' + node + '"' in body


def test_the_prompts_do_not_ask_for_numbers_the_contract_forbids():
    import interpretation_prompts as ip
    for node, body in ip.SPECIALIST_PROMPTS.items():
        low = body.lower()
        assert "already been computed" in low or "already computed" in low, node
        assert "do not compute" in low, node


def test_the_verifier_prompt_offers_exactly_the_three_contract_verdicts():
    import interpretation_prompts as ip
    body = ip.VERIFIER
    for verdict in ic.VERDICTS:
        assert f'"{verdict}"' in body
    assert "refute" in body.lower()


def test_the_synthesis_prompt_honours_the_readiness_gate():
    import interpretation_prompts as ip
    body = " ".join(ip.SYNTHESIS.lower().split())
    assert "recommendations_withheld" in body
    assert "not yours to reopen" in body
    assert "based_on_finding_ids" in ip.SYNTHESIS
    # It must not be handed, or ask for, raw numbers.
    assert "you are not given the underlying numbers" in body
