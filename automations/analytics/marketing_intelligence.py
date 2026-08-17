#!/usr/bin/env python3
"""
`marketing_intelligence.json` — the Analytics -> Marketing Strategy handoff.

This is the boundary object. Everything upstream of it is measurement and
interpretation; everything downstream is strategy. It is deliberately the
*only* thing a strategy agent should need to read, and deliberately not a
place raw analytics can leak through: it carries findings that survived
verification, the readiness state that governs whether advice is allowed at
all, and an explicit account of what was not covered.

Three properties a consumer can rely on:

  * **Nothing here is unverified.** Every finding either was backed
    deterministically (an observation) or passed an independent verifier.
    Findings that were rejected, or that the verifier budget never reached,
    appear under `excluded_findings` with the reason — visible, not deleted,
    because "we could not check this" is information a strategist needs.

  * **Completeness is stated, never implied.** If Clarity had no data the
    status is `partial`, the UX domain is listed as uncovered, and no part of
    the document pretends otherwise. There is no fallback value anywhere in
    this file.

  * **The readiness gate survives the handoff.** If the analysis withheld
    recommendations because the site is below the volume threshold, this
    document carries that decision and `priorities` is empty. The strategy
    layer is told advice was withheld and why — not handed a blank field it
    might read as "nothing to do".
"""

import datetime as dt

import client_config
import interpretation_contracts as ic
import interpretation_graph as ig
from analysis_model import READY

SCHEMA_VERSION = "1.0.0"

#: The document kind is `<client_slug>.marketing_intelligence`. The suffix is
#: the contract; the slug says whose. Resolved per call rather than frozen at
#: import so a process serving two clients cannot leak one into the other's
#: document.
KIND_SUFFIX = "marketing_intelligence"


def document_kind(slug=None, env=None):
    return client_config.namespaced(KIND_SUFFIX, slug=slug, env=env)

#: Which specialist covers which strategy domain. Used to say plainly which
#: domains are uncovered when a node was skipped or failed.
DOMAIN_OF = {
    ig.NODE_TRAFFIC: "acquisition",
    ig.NODE_SEO: "search",
    ig.NODE_UX: "experience",
    ig.NODE_CONVERSION: "conversion",
}


def _finding_out(finding):
    out = {
        "id": finding["id"],
        "domain": DOMAIN_OF.get(finding["node"], finding["node"]),
        "node": finding["node"],
        "kind": finding["kind"],
        "statement": finding["statement"],
        "confidence": finding["confidence"],
        "severity": finding["severity"],
        "evidence_fact_ids": finding["evidence_fact_ids"],
        "alternative_explanations": finding.get("alternative_explanations", []),
        "verification": finding.get("verification", {}),
    }
    if "downgraded_from" in finding:
        out["downgraded_from"] = finding["downgraded_from"]
    if "excluded_because" in finding:
        out["excluded_because"] = finding["excluded_because"]
        out["detail"] = finding.get("detail")
    return out


def uncovered_domains(manifest):
    """Domains with no verified coverage, and why — never silently omitted."""
    detail = manifest["specialists"]["detail"]
    out = []
    for node, entry in detail.items():
        if entry["status"] == ic.STATUS_OK:
            continue
        out.append({
            "domain": DOMAIN_OF.get(node, node),
            "node": node,
            "status": entry["status"],
            "reason": entry.get("reason") or entry.get("error")
                      or "node did not produce a valid result",
            "missing_sources": entry.get("missing_sources", []),
        })
    return out


def build(document, graph_result, now=None, client_slug=None):
    """Assemble the handoff from a finished report and a completed graph run."""
    manifest = graph_result["manifest"]
    synthesis = graph_result.get("synthesis") or {}
    readiness = document.get("readiness")
    withheld = readiness != READY

    verified = [_finding_out(f) for f in graph_result["verified_findings"]]
    excluded = [_finding_out(f) for f in graph_result["excluded_findings"]]

    # Priorities are derived from verified findings, and only when the
    # analysis layer permitted advice at all. This layer never re-opens that
    # decision — it is the readiness gate, honoured across the boundary.
    priorities = []
    if not withheld:
        for finding in sorted(
                graph_result["verified_findings"],
                key=lambda f: (-ic.SEVERITY_ORDER[f["severity"]],
                               -ic.CONFIDENCE_ORDER[f["confidence"]], f["id"])):
            if finding["severity"] in (ic.SEV_HIGH, ic.SEV_MEDIUM):
                priorities.append({
                    "finding_id": finding["id"],
                    "domain": DOMAIN_OF.get(finding["node"], finding["node"]),
                    "severity": finding["severity"],
                    "confidence": finding["confidence"],
                    "statement": finding["statement"],
                })

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": document_kind(client_slug),
        "generated_at": (now or dt.datetime.now(dt.timezone.utc))
                        .replace(microsecond=0).isoformat(),

        # Where this came from. A consumer that wants the underlying numbers
        # resolves them here rather than being handed a copy that can drift.
        "report_ref": {
            "report_date": document.get("report_date"),
            "report_kind": document.get("kind"),
            "report_schema_version": document.get("schema_version"),
            "json_key": (document.get("storage") or {}).get("json_key"),
            "period": document.get("period"),
            "comparison_period": document.get("comparison_period"),
        },

        # The gate, carried across the boundary intact.
        "readiness": {
            "state": readiness,
            "recommendations_withheld": withheld,
            "note": document.get("readiness_note", ""),
            "meaning": ("Advice was withheld by the analysis layer's readiness "
                        "gate. This is a valid result, not an error, and must "
                        "not be worked around downstream."
                        if withheld else
                        "The analysis layer permitted recommendations."),
        },

        # What was and was not covered. Derived, not asserted.
        "completeness": {
            "status": manifest["status"],
            "sources_available": manifest["sources"]["available"],
            "sources_missing": manifest["sources"]["missing"],
            "specialists_ran": manifest["specialists"]["ran"],
            "specialists_skipped": manifest["specialists"]["skipped_missing_input"],
            "specialists_failed": manifest["specialists"]["failed"],
            "uncovered_domains": uncovered_domains(manifest),
        },

        "verified_findings": verified,
        "excluded_findings": excluded,
        "themes": synthesis.get("themes", []),
        "open_questions": synthesis.get("open_questions", []),
        "priorities": priorities,

        "provenance": {
            "manifest_id": manifest["manifest_id"],
            "graph_version": manifest["graph_version"],
            "contract_version": manifest["contract_version"],
            "budget": manifest["budget"],
            "generated_from": "verified findings only; no raw API payloads",
        },

        "consumer_contract": {
            "refuse_unknown_schema_version": True,
            "never_treat_partial_as_complete": True,
            "never_reopen_readiness_gate": True,
            "excluded_findings_are_not_evidence": True,
        },
    }


def validate(doc):
    """Assert the properties a strategy agent is entitled to assume.

    Kept as a function rather than a comment because the handoff is the one
    artifact another system builds on, and a promise that is only written in
    prose is one nobody can check.
    """
    problems = []
    if doc.get("schema_version") != SCHEMA_VERSION:
        problems.append("schema_version mismatch")
    kind = doc.get("kind") or ""
    if not kind.endswith("." + KIND_SUFFIX) or kind.startswith("."):
        problems.append(f"kind {kind!r} is not <client_slug>.{KIND_SUFFIX}")
    for key in ("kind", "generated_at", "report_ref", "readiness",
                "completeness", "verified_findings", "excluded_findings",
                "themes", "priorities", "provenance"):
        if key not in doc:
            problems.append(f"missing required key {key!r}")

    completeness = doc.get("completeness", {})
    if completeness.get("status") not in (ig.RUN_COMPLETE, ig.RUN_PARTIAL):
        problems.append("completeness.status must be complete or partial")
    if completeness.get("status") == ig.RUN_COMPLETE:
        if completeness.get("sources_missing"):
            problems.append("status complete while sources are missing")
        if completeness.get("specialists_skipped") or completeness.get(
                "specialists_failed"):
            problems.append("status complete while a specialist did not run")

    if doc.get("readiness", {}).get("recommendations_withheld") and doc.get("priorities"):
        problems.append("priorities present although recommendations were withheld")

    for finding in doc.get("verified_findings", []):
        if not finding.get("evidence_fact_ids"):
            problems.append(f"{finding.get('id')}: verified finding without evidence")
        if not finding.get("verification"):
            problems.append(f"{finding.get('id')}: verified finding without a verdict")
        if finding.get("verification", {}).get("verdict") == ic.VERDICT_REJECTED:
            problems.append(f"{finding.get('id')}: rejected finding in verified_findings")

    allowed = {f["id"] for f in doc.get("verified_findings", [])}
    for theme in doc.get("themes", []):
        unknown = [b for b in theme.get("based_on_finding_ids", [])
                   if b not in allowed]
        if unknown:
            problems.append(f"theme {theme.get('title')!r} cites unverified {unknown}")

    return problems
