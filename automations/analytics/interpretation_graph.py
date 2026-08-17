#!/usr/bin/env python3
r"""
The interpretation graph: four bounded specialists, selective verification,
one synthesis.

    report document (produced by the existing pipeline, unchanged)
                    |
              slice_inputs()          <- code. deterministic. no model call.
       ___________/ | | \___________
      /            /   \            \
  traffic       seo     ux      conversion   <- 4 specialists, NO edges between them
   (ga4)       (gsc)  (clarity)  (ga4+quality)
      \____________ | | ____________/
                    |
        judgment findings only                <- observations skip verification
                    |
              verifier (<= 6)                  <- one call per selected judgment
                    |
         findings that survived
                    |
              synthesis (1)                    <- verified findings, never raw payloads
                    |
        marketing_intelligence.json

The specialists genuinely do not depend on one another, so the graph does not
pretend they do. Each reads its own slice and nothing else, which is what
makes "traffic ran but clarity had no data" a describable state rather than a
cascade failure. Adding an edge that only exists to sequence the calls would
be a lie about the dependency structure, and the manifest would inherit it.

WHAT THIS LAYER DOES NOT DO

It does not collect, normalize, store, threshold, classify anomalies, gate
recommendations, render a report, or publish a dashboard. All of that already
exists and is untouched. This layer reads a finished analysis document and
adds interpretation on top of it.

In particular it never recomputes significance or eligibility. It reads
`fact.significant` and `fact.meets_minimum` as given, so every threshold in
thresholds.py continues to decide what counts — and if a report withheld
recommendations under the readiness gate, this layer withholds them too.

BUDGETS

Hard caps, enforced by a counter that raises rather than by convention:
4 specialist calls (one per specialist), 6 verifier calls, 1 synthesis call.
A malformed response may be retried once per node; retries are counted and
reported separately so the cap on distinct calls stays exactly what it says.
"""

import datetime as dt
import hashlib
import json

import interpretation_contracts as ic
from analysis_model import INSUFFICIENT_DATA, READY
from records import CLARITY, GA4, GSC

GRAPH_VERSION = "1.0.0"

# --- hard budgets ----------------------------------------------------------
MAX_SPECIALIST_CALLS = 4
MAX_VERIFIER_CALLS = 6
MAX_SYNTHESIS_CALLS = 1
MAX_RETRIES_PER_NODE = 1

# --- node names ------------------------------------------------------------
NODE_TRAFFIC = "traffic"
NODE_SEO = "seo"
NODE_UX = "ux"
NODE_CONVERSION = "conversion"
SPECIALISTS = (NODE_TRAFFIC, NODE_SEO, NODE_UX, NODE_CONVERSION)

NODE_VERIFIER = "verifier"
NODE_SYNTHESIS = "synthesis"

#: Which sources each specialist needs before it can say anything at all.
#: A specialist whose sources are absent is skipped explicitly — never run
#: against an empty slice so it can produce confident nothing.
REQUIRED_SOURCES = {
    NODE_TRAFFIC: (GA4,),
    NODE_SEO: (GSC,),
    NODE_UX: (CLARITY,),
    NODE_CONVERSION: (GA4,),
}

RUN_COMPLETE = "complete"
RUN_PARTIAL = "partial"


class BudgetExceeded(RuntimeError):
    """A node tried to make a call the budget does not allow."""


class CallBudget:
    """Counts calls per role and refuses to go over.

    Retries are counted, but against their own allowance: 'max 4 specialist
    calls' has to keep meaning four specialists, not three specialists and a
    retry.
    """

    def __init__(self, specialists=MAX_SPECIALIST_CALLS,
                 verifiers=MAX_VERIFIER_CALLS,
                 synthesis=MAX_SYNTHESIS_CALLS,
                 retries_per_node=MAX_RETRIES_PER_NODE):
        self.caps = {"specialist": specialists, "verifier": verifiers,
                     "synthesis": synthesis}
        self.used = {"specialist": 0, "verifier": 0, "synthesis": 0}
        self.retries = {}
        self.retries_per_node = retries_per_node

    def spend(self, role):
        if self.used[role] >= self.caps[role]:
            raise BudgetExceeded(
                f"{role} budget exhausted ({self.caps[role]} calls)")
        self.used[role] += 1

    def can_retry(self, node):
        return self.retries.get(node, 0) < self.retries_per_node

    def spend_retry(self, node):
        if not self.can_retry(node):
            raise BudgetExceeded(f"{node}: retry budget exhausted")
        self.retries[node] = self.retries.get(node, 0) + 1

    def remaining(self, role):
        return self.caps[role] - self.used[role]

    def to_dict(self):
        return {
            "caps": dict(self.caps),
            "calls_made": dict(self.used),
            "retries": dict(self.retries),
            "total_calls": sum(self.used.values()) + sum(self.retries.values()),
        }


# --------------------------------------------------------------------------
# Input slicing — deterministic, no model involved
# --------------------------------------------------------------------------

def _facts(document):
    return document.get("facts", []) or []


def available_sources(document):
    """Sources that actually contributed facts to this report."""
    return {f.get("source") for f in _facts(document) if f.get("source")}


def slice_inputs(document):
    """Build each specialist's bounded input from the finished report.

    Bounded in the literal sense: a node is handed the facts for its own
    sources and nothing else, so the contract check that evidence must
    resolve to the slice has real teeth. A traffic node cannot cite a Clarity
    fact because it was never given one.
    """
    facts = _facts(document)
    by_source = {}
    for fact in facts:
        by_source.setdefault(fact.get("source"), []).append(fact)

    quality = document.get("data_quality", {}) or {}
    period = {"period": document.get("period"),
              "comparison_period": document.get("comparison_period")}

    slices = {
        NODE_TRAFFIC: {
            "facts": by_source.get(GA4, []),
            "context": {**period,
                        "tracking_coverage": document.get("tracking_coverage", {})},
        },
        NODE_SEO: {
            "facts": by_source.get(GSC, []),
            "context": {**period},
        },
        NODE_UX: {
            "facts": by_source.get(CLARITY, []),
            "context": {**period,
                        "clarity_ledger": (document.get("source_coverage", {})
                                           or {}).get("clarity_ledger", {})},
        },
        # Conversion reads GA4 facts plus the tracking boundary, because a
        # purchase count means nothing without knowing whether purchases were
        # being tracked in that window.
        NODE_CONVERSION: {
            "facts": by_source.get(GA4, []),
            "context": {
                **period,
                "conversions": document.get("conversions", quality.get("conversions", {})),
                "ecommerce_tracking_boundary": document.get(
                    "ecommerce_tracking_boundary",
                    quality.get("ecommerce_boundary", {})),
            },
        },
    }
    for name, payload in slices.items():
        payload["node"] = name
        payload["fact_ids"] = [f.get("id") for f in payload["facts"]]
    return slices


def runnable(node, document):
    """Whether a specialist has the sources it needs.

    A node with no facts is skipped rather than run. Running it would produce
    an empty result indistinguishable from 'looked and found nothing', and
    those are very different things to hand a strategy agent.
    """
    present = available_sources(document)
    required = REQUIRED_SOURCES[node]
    missing = [s for s in required if s not in present]
    return (not missing), missing


# --------------------------------------------------------------------------
# Verification selection
# --------------------------------------------------------------------------

def select_for_verification(findings, limit=MAX_VERIFIER_CALLS):
    """Judgments only, worst-first, capped.

    Observations are already backed by deterministic facts; spending a
    verifier call on one would buy a second opinion on arithmetic. Among
    judgments, the ranking puts high severity and low confidence first —
    the combination most likely to be both wrong and consequential.
    """
    judgments = [f for f in findings if f["kind"] == ic.JUDGMENT]
    ranked = sorted(
        judgments,
        key=lambda f: (-ic.SEVERITY_ORDER[f["severity"]],
                       ic.CONFIDENCE_ORDER[f["confidence"]],
                       f["id"]),
    )
    return ranked[:limit], ranked[limit:]


# --------------------------------------------------------------------------
# Node execution
# --------------------------------------------------------------------------

def _call_with_retry(caller, node, request, validate, budget, role, manifest_entry):
    """One call, one retry on a contract failure, then give up honestly."""
    attempts = []
    while True:
        budget.spend(role) if not attempts else budget.spend_retry(node)
        try:
            raw = caller(node, request)
        except Exception as exc:  # noqa: BLE001 — a caller failure is a node failure
            attempts.append({"error": f"{type(exc).__name__}: {exc}"})
            manifest_entry["attempts"] = attempts
            manifest_entry["status"] = ic.STATUS_FAILED_ERROR
            manifest_entry["error"] = attempts[-1]["error"]
            return None
        try:
            result = validate(raw)
        except ic.ContractError as exc:
            attempts.append({"contract_error": str(exc)})
            if budget.can_retry(node):
                continue
            manifest_entry["attempts"] = attempts
            manifest_entry["status"] = ic.STATUS_FAILED_CONTRACT
            manifest_entry["error"] = str(exc)
            return None
        attempts.append({"ok": True})
        manifest_entry["attempts"] = attempts
        manifest_entry["status"] = ic.STATUS_OK
        return result


def run_specialists(document, caller, budget, slices=None):
    """Run the four specialists. Independent — order here is not a dependency."""
    slices = slices or slice_inputs(document)
    results, manifest = {}, {}

    for node in SPECIALISTS:
        entry = {"node": node, "role": "specialist"}
        ok, missing = runnable(node, document)
        if not ok:
            entry.update({
                "status": ic.STATUS_SKIPPED_NO_INPUT,
                "missing_sources": missing,
                "attempts": [],
                "reason": (f"no {'/'.join(missing)} facts in this report; the node "
                           f"was not called"),
            })
            manifest[node] = entry
            continue

        node_slice = slices[node]
        allowed = set(node_slice["fact_ids"])
        facts_by_id = {f.get("id"): f for f in node_slice["facts"]}
        entry["input_fact_count"] = len(allowed)

        result = _call_with_retry(
            caller, node, node_slice,
            lambda raw, n=node, a=allowed, fb=facts_by_id:
                ic.validate_specialist(raw, n, a, fb),
            budget, "specialist", entry)

        if result is not None:
            results[node] = result
            entry["finding_count"] = len(result["findings"])
            entry["unable_to_assess"] = result["unable_to_assess"]
        manifest[node] = entry

    return results, manifest


def run_verification(specialist_results, caller, budget):
    """Verify the judgments that matter most, within budget."""
    all_findings = [f for r in specialist_results.values() for f in r["findings"]]
    selected, unselected = select_for_verification(
        all_findings, limit=budget.remaining("verifier"))

    verified, excluded, manifest = [], [], []

    # Observations pass straight through — nothing to second-guess.
    for finding in all_findings:
        if finding["kind"] == ic.OBSERVATION:
            passed = dict(finding)
            passed["verification"] = {"verdict": "not_required",
                                      "reason": "observation backed by facts"}
            verified.append(passed)

    for finding in selected:
        entry = {"node": NODE_VERIFIER, "role": "verifier",
                 "finding_id": finding["id"]}
        result = _call_with_retry(
            caller, NODE_VERIFIER,
            {"finding": finding, "task": "refute_or_confirm"},
            lambda raw, fid=finding["id"]: ic.validate_verdict(raw, fid),
            budget, "verifier", entry)
        manifest.append(entry)

        if result is None:
            excluded.append({**finding, "excluded_because": ic.EXCLUDED_UNVERIFIED,
                             "detail": entry.get("error")})
            continue
        entry["verdict"] = result["verdict"]
        if result["verdict"] == ic.VERDICT_REJECTED:
            excluded.append({**ic.apply_verdict(finding, result),
                             "excluded_because": ic.EXCLUDED_REJECTED})
        else:
            verified.append(ic.apply_verdict(finding, result))

    for finding in unselected:
        excluded.append({**finding, "excluded_because": ic.EXCLUDED_UNVERIFIED,
                         "detail": "verifier budget did not reach this finding"})

    return verified, excluded, manifest


def run_synthesis(verified, document, caller, budget):
    """One call, over verified findings only.

    The request deliberately carries no facts, no API payloads and no raw
    metrics — only findings that already survived verification, plus the
    readiness state. If synthesis could see the raw numbers it would start
    computing again, and the layer below would stop being the single place
    arithmetic happens.
    """
    entry = {"node": NODE_SYNTHESIS, "role": "synthesis"}
    if not verified:
        entry.update({"status": ic.STATUS_SKIPPED_NO_INPUT, "attempts": [],
                      "reason": "no finding survived verification"})
        return None, entry

    allowed = {f["id"] for f in verified}
    request = {
        "findings": [
            {k: f[k] for k in ("id", "node", "kind", "statement", "confidence",
                               "severity", "alternative_explanations")}
            for f in verified
        ],
        "readiness": document.get("readiness"),
        "recommendations_withheld": document.get("readiness") != READY,
    }
    result = _call_with_retry(
        caller, NODE_SYNTHESIS, request,
        lambda raw, a=allowed: ic.validate_synthesis(raw, a),
        budget, "synthesis", entry)
    return result, entry


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------

def manifest_id(document):
    basis = f"{document.get('report_date')}|{GRAPH_VERSION}"
    return "mf_" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:12]


def build_manifest(document, specialist_manifest, verifier_manifest,
                   synthesis_entry, budget, now=None):
    """A deterministic account of what ran, what did not, and why.

    Completeness is derived from node outcomes rather than asserted, so a run
    cannot be described as complete while a node is missing.
    """
    present = sorted(available_sources(document))
    expected = [GA4, GSC, CLARITY]
    missing = [s for s in expected if s not in present]

    node_states = {name: entry["status"] for name, entry in specialist_manifest.items()}
    ran = [n for n, s in node_states.items() if s == ic.STATUS_OK]
    skipped = [n for n, s in node_states.items() if s == ic.STATUS_SKIPPED_NO_INPUT]
    failed = [n for n, s in node_states.items()
              if s in (ic.STATUS_FAILED_CONTRACT, ic.STATUS_FAILED_ERROR)]

    status = RUN_COMPLETE if (len(ran) == len(SPECIALISTS) and not missing) \
        else RUN_PARTIAL

    return {
        "manifest_id": manifest_id(document),
        "graph_version": GRAPH_VERSION,
        "contract_version": ic.CONTRACT_VERSION,
        "generated_at": (now or dt.datetime.now(dt.timezone.utc))
                        .replace(microsecond=0).isoformat(),
        "report_date": document.get("report_date"),
        "status": status,
        "sources": {"expected": expected, "available": present, "missing": missing},
        "specialists": {
            "expected": list(SPECIALISTS),
            "ran": sorted(ran),
            "skipped_missing_input": sorted(skipped),
            "failed": sorted(failed),
            "detail": specialist_manifest,
        },
        "verification": {
            "calls": verifier_manifest,
            "verified_count": sum(1 for e in verifier_manifest if e.get("verdict")),
        },
        "synthesis": synthesis_entry,
        "budget": budget.to_dict(),
    }


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def run_graph(document, caller, now=None, budget=None):
    """Execute the whole graph over one finished report document.

    `caller(node_name, request) -> dict` is the only outside dependency. No
    live caller is wired anywhere in this change: the graph is exercised by
    deterministic fixtures, and nothing in this module reaches production.
    """
    budget = budget or CallBudget()
    slices = slice_inputs(document)

    specialist_results, specialist_manifest = run_specialists(
        document, caller, budget, slices)
    verified, excluded, verifier_manifest = run_verification(
        specialist_results, caller, budget)
    synthesis, synthesis_entry = run_synthesis(verified, document, caller, budget)
    manifest = build_manifest(document, specialist_manifest, verifier_manifest,
                              synthesis_entry, budget, now=now)

    return {
        "manifest": manifest,
        "verified_findings": verified,
        "excluded_findings": excluded,
        "synthesis": synthesis,
    }


def to_json(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False)
