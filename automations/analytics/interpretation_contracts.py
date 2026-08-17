#!/usr/bin/env python3
"""
The JSON contracts every interpretation node must satisfy, and their checker.

The interpretation layer is the first place in this system where a
*judgment* is produced rather than a measurement. Everything below it —
collection, normalization, thresholds, significance, anomaly classification,
recommendation gating — is deterministic code and stays that way. This module
exists to stop the judgment layer from quietly reaching back down and
inventing the parts that were supposed to be measured.

Four invariants, all enforced at validation rather than requested in a prompt:

  1. **Evidence must resolve.** Every finding cites fact ids, and every cited
     id must be present in the slice that node was actually given. A node
     cannot reference a fact it was never shown, which is the cheapest
     possible defence against a confidently invented one.

  2. **Numbers must come from the facts.** Any number appearing in a
     finding's prose must be derivable from the evidence it cites. This is
     the rule that keeps deterministic calculation in code: a node may say
     what a movement means, but it may not decide what the movement was.

  3. **No causal language.** Reused verbatim from analysis_model, so the
     interpretation layer is held to the same standard as the analysis layer
     rather than a parallel one that can drift.

  4. **Judgments must be falsifiable.** A finding marked as judgment has to
     offer at least one alternative explanation, and only judgments are
     eligible for verification. Observations are already backed by
     deterministic facts and verifying them would spend budget re-proving
     arithmetic.

A node whose output fails any of these is malformed. It is not repaired, not
partially accepted, and not silently dropped: it is reported, retried once,
and if it fails again the node is recorded as failed and the run continues as
explicitly incomplete.
"""

import re

from analysis_model import (CONFIDENCE_LEVELS, HIGH, LOW, MEDIUM,
                            _CAUSAL_PATTERNS)

CONTRACT_VERSION = "1.0.0"

# --- finding kinds ---------------------------------------------------------
#: Backed directly by deterministic facts. Needs no verification.
OBSERVATION = "observation"
#: An interpretation. Verifiable, and only these are ever sent to a verifier.
JUDGMENT = "judgment"
FINDING_KINDS = (OBSERVATION, JUDGMENT)

# --- severity --------------------------------------------------------------
SEV_HIGH = "high"
SEV_MEDIUM = "medium"
SEV_LOW = "low"
SEV_INFO = "info"
SEVERITIES = (SEV_HIGH, SEV_MEDIUM, SEV_LOW, SEV_INFO)

# --- node status -----------------------------------------------------------
STATUS_OK = "ok"
STATUS_SKIPPED_NO_INPUT = "skipped_missing_input"
STATUS_FAILED_CONTRACT = "failed_contract"
STATUS_FAILED_ERROR = "failed_error"
NODE_STATUSES = (STATUS_OK, STATUS_SKIPPED_NO_INPUT,
                 STATUS_FAILED_CONTRACT, STATUS_FAILED_ERROR)

# --- verifier verdicts -----------------------------------------------------
VERDICT_CONFIRMED = "confirmed"
VERDICT_DOWNGRADED = "downgraded"
VERDICT_REJECTED = "rejected"
VERDICTS = (VERDICT_CONFIRMED, VERDICT_DOWNGRADED, VERDICT_REJECTED)

#: Why a judgment finding never reached synthesis.
EXCLUDED_REJECTED = "verifier_rejected"
EXCLUDED_UNVERIFIED = "unverified_budget_exhausted"

CONFIDENCE_ORDER = {LOW: 0, MEDIUM: 1, HIGH: 2}
SEVERITY_ORDER = {SEV_INFO: 0, SEV_LOW: 1, SEV_MEDIUM: 2, SEV_HIGH: 3}

_NUMBER_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


class ContractError(ValueError):
    """A node returned something that does not satisfy its contract."""


# --------------------------------------------------------------------------
# number provenance
# --------------------------------------------------------------------------

def _numbers(text):
    out = []
    for raw in _NUMBER_RE.findall(text or ""):
        try:
            out.append(float(raw.replace(",", ".")))
        except ValueError:
            continue
    return out


def evidence_numbers(facts):
    """Every number a node is entitled to state, given the facts it cites.

    Includes the percentage rendering of a fractional delta, because a report
    that says "fell 18%" from delta_pct=-0.18 is quoting its evidence
    correctly and should not be called a fabrication.
    """
    allowed = set()
    for fact in facts:
        for key in ("period_value", "comparison_value", "delta_abs",
                    "delta_pct", "sample_size", "comparison_sample_size"):
            value = fact.get(key) if isinstance(fact, dict) else getattr(fact, key, None)
            if value is None:
                continue
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            allowed.add(abs(value))
            if key in ("delta_pct",):
                allowed.add(abs(value * 100.0))
    return allowed


def unsupported_numbers(statement, facts, tolerance=0.05):
    """Numbers in the prose that the cited facts cannot account for.

    Matching is deliberately generous — rounding, a percentage written either
    way, and small formatting differences all pass — because the target is
    invention, not imprecision. Years and other small integers that appear in
    every period label would otherwise dominate the output, so exact integer
    matches against period text are allowed through by the caller.
    """
    allowed = evidence_numbers(facts)
    missing = []
    for number in _numbers(statement):
        value = abs(number)
        if any(abs(value - candidate) <= max(tolerance, abs(candidate) * tolerance)
               for candidate in allowed):
            continue
        # A rounded quotation of a permitted value.
        if any(round(candidate) == round(value) for candidate in allowed):
            continue
        missing.append(number)
    return missing


# --------------------------------------------------------------------------
# specialist output
# --------------------------------------------------------------------------

def validate_specialist(payload, node_name, allowed_fact_ids, facts_by_id):
    """Return a normalized specialist result, or raise ContractError.

    `allowed_fact_ids` is the slice this node was handed. Citing anything
    outside it is the failure mode this whole function exists for.
    """
    if not isinstance(payload, dict):
        raise ContractError(f"{node_name}: expected a JSON object, got "
                            f"{type(payload).__name__}")

    node = payload.get("node")
    if node != node_name:
        raise ContractError(f"{node_name}: payload declares node={node!r}")

    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ContractError(f"{node_name}: 'findings' must be a list")

    seen_ids = set()
    normalized = []
    for index, raw in enumerate(findings):
        normalized.append(
            _validate_finding(raw, node_name, index, allowed_fact_ids,
                              facts_by_id, seen_ids))

    unable = payload.get("unable_to_assess", [])
    if not isinstance(unable, list) or any(not isinstance(u, str) for u in unable):
        raise ContractError(f"{node_name}: 'unable_to_assess' must be a list of strings")

    return {
        "node": node_name,
        "contract_version": CONTRACT_VERSION,
        "status": STATUS_OK,
        "findings": normalized,
        "unable_to_assess": unable,
    }


def _validate_finding(raw, node_name, index, allowed_fact_ids, facts_by_id, seen_ids):
    where = f"{node_name}.findings[{index}]"
    if not isinstance(raw, dict):
        raise ContractError(f"{where}: not an object")

    finding_id = raw.get("id")
    if not isinstance(finding_id, str) or not finding_id.strip():
        raise ContractError(f"{where}: missing 'id'")
    if finding_id in seen_ids:
        raise ContractError(f"{where}: duplicate id {finding_id!r}")
    seen_ids.add(finding_id)

    kind = raw.get("kind")
    if kind not in FINDING_KINDS:
        raise ContractError(f"{where}: kind must be one of {FINDING_KINDS}, got {kind!r}")

    statement = raw.get("statement")
    if not isinstance(statement, str) or not statement.strip():
        raise ContractError(f"{where}: missing 'statement'")

    # Invariant 3 — same rule the analysis layer enforces.
    match = _CAUSAL_PATTERNS.search(statement)
    if match:
        raise ContractError(
            f"{where}: causal language {match.group(0)!r} in statement. This "
            f"data supports 'moved together', never 'made it happen'.")

    confidence = raw.get("confidence", MEDIUM)
    if confidence not in CONFIDENCE_LEVELS:
        raise ContractError(f"{where}: confidence must be one of {CONFIDENCE_LEVELS}")

    severity = raw.get("severity", SEV_INFO)
    if severity not in SEVERITIES:
        raise ContractError(f"{where}: severity must be one of {SEVERITIES}")

    # Invariant 1 — evidence must resolve to the slice this node was given.
    evidence = raw.get("evidence_fact_ids")
    if not isinstance(evidence, list) or not evidence:
        raise ContractError(f"{where}: 'evidence_fact_ids' must be a non-empty list")
    unknown = [e for e in evidence if e not in allowed_fact_ids]
    if unknown:
        raise ContractError(
            f"{where}: cites fact id(s) not in this node's input slice: {unknown}")

    # Invariant 4 — a judgment has to be arguable with.
    alternatives = raw.get("alternative_explanations", [])
    if not isinstance(alternatives, list) or any(
            not isinstance(a, str) for a in alternatives):
        raise ContractError(f"{where}: 'alternative_explanations' must be a list of strings")
    if kind == JUDGMENT and not alternatives:
        raise ContractError(
            f"{where}: a judgment must offer at least one alternative explanation")

    # Invariant 2 — numbers come from the facts.
    cited = [facts_by_id[e] for e in evidence if e in facts_by_id]
    missing = unsupported_numbers(statement, cited)
    if missing:
        raise ContractError(
            f"{where}: statement contains number(s) {missing} not supported by "
            f"its cited facts. Deterministic values stay in code.")

    return {
        "id": finding_id,
        "node": node_name,
        "kind": kind,
        "statement": statement.strip(),
        "confidence": confidence,
        "severity": severity,
        "evidence_fact_ids": list(evidence),
        "alternative_explanations": list(alternatives),
    }


# --------------------------------------------------------------------------
# verifier output
# --------------------------------------------------------------------------

def validate_verdict(payload, finding_id):
    if not isinstance(payload, dict):
        raise ContractError(f"verifier[{finding_id}]: expected a JSON object")
    if payload.get("finding_id") != finding_id:
        raise ContractError(
            f"verifier[{finding_id}]: verdict is for {payload.get('finding_id')!r}")

    verdict = payload.get("verdict")
    if verdict not in VERDICTS:
        raise ContractError(
            f"verifier[{finding_id}]: verdict must be one of {VERDICTS}, got {verdict!r}")

    reason = payload.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ContractError(f"verifier[{finding_id}]: missing 'reason'")

    confidence = payload.get("confidence", MEDIUM)
    if confidence not in CONFIDENCE_LEVELS:
        raise ContractError(f"verifier[{finding_id}]: bad confidence {confidence!r}")

    return {
        "finding_id": finding_id,
        "verdict": verdict,
        "reason": reason.strip(),
        "confidence": confidence,
    }


def apply_verdict(finding, verdict):
    """Fold a verdict into the finding. Downgrade lowers confidence one step."""
    result = dict(finding)
    result["verification"] = {
        "verdict": verdict["verdict"],
        "reason": verdict["reason"],
        "verifier_confidence": verdict["confidence"],
    }
    if verdict["verdict"] == VERDICT_DOWNGRADED:
        order = CONFIDENCE_ORDER[finding["confidence"]]
        result["confidence"] = {0: LOW, 1: LOW, 2: MEDIUM}[order]
        result["downgraded_from"] = finding["confidence"]
    return result


# --------------------------------------------------------------------------
# synthesis output
# --------------------------------------------------------------------------

def validate_synthesis(payload, allowed_finding_ids):
    """Synthesis may only build on findings that survived verification."""
    if not isinstance(payload, dict):
        raise ContractError("synthesis: expected a JSON object")

    themes = payload.get("themes")
    if not isinstance(themes, list):
        raise ContractError("synthesis: 'themes' must be a list")

    normalized = []
    for index, raw in enumerate(themes):
        where = f"synthesis.themes[{index}]"
        if not isinstance(raw, dict):
            raise ContractError(f"{where}: not an object")
        title = raw.get("title")
        if not isinstance(title, str) or not title.strip():
            raise ContractError(f"{where}: missing 'title'")
        narrative = raw.get("narrative")
        if not isinstance(narrative, str) or not narrative.strip():
            raise ContractError(f"{where}: missing 'narrative'")
        match = _CAUSAL_PATTERNS.search(narrative)
        if match:
            raise ContractError(f"{where}: causal language {match.group(0)!r}")
        based_on = raw.get("based_on_finding_ids")
        if not isinstance(based_on, list) or not based_on:
            raise ContractError(f"{where}: 'based_on_finding_ids' must be non-empty")
        unknown = [b for b in based_on if b not in allowed_finding_ids]
        if unknown:
            raise ContractError(
                f"{where}: cites finding id(s) that did not survive verification: "
                f"{unknown}")
        normalized.append({
            "title": title.strip(),
            "narrative": narrative.strip(),
            "based_on_finding_ids": list(based_on),
        })

    questions = payload.get("open_questions", [])
    if not isinstance(questions, list) or any(
            not isinstance(q, str) for q in questions):
        raise ContractError("synthesis: 'open_questions' must be a list of strings")

    return {
        "contract_version": CONTRACT_VERSION,
        "themes": normalized,
        "open_questions": questions,
    }
