#!/usr/bin/env python3
"""
The analysis-layer schema: facts, inferences, anomalies, recommendations.

This is the L2 model. Phase 1's MetricRecord is a measurement; a Fact here is a
measurement *compared against something*, which is what an analysis reasons
over.

The central structural decision: **facts and inferences are separate types**,
and an inference cannot be constructed without referencing the fact ids it
rests on. That makes "separate what was measured from what was interpreted" a
property of the schema rather than a writing convention that erodes.

Inferences additionally:
  * carry causal_claim=False as an invariant,
  * must list at least one alternative explanation,
  * are rejected at construction if their statement uses causal language.

The last one is deliberately blunt. A sentence like "the redesign caused the
drop" is unfalsifiable from this data, and the cheapest place to stop it is
before it exists.
"""

import datetime as dt
import hashlib
import re
from dataclasses import asdict, dataclass, field

# --- readiness / confidence -----------------------------------------------
READY = "ready"
INSUFFICIENT_DATA = "insufficient_data"
SUPPRESSED = "suppressed"
READINESS_STATES = (READY, INSUFFICIENT_DATA, SUPPRESSED)

HIGH = "high"
MEDIUM = "medium"
LOW = "low"
CONFIDENCE_LEVELS = (HIGH, MEDIUM, LOW)

# --- priorities ------------------------------------------------------------
PRIORITY_HIGH = "High"
PRIORITY_MEDIUM = "Medium"
PRIORITY_MONITOR = "Monitor"
PRIORITIES = (PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_MONITOR)

# --- anomaly classes -------------------------------------------------------
PERFORMANCE_ANOMALY = "performance"
INSTRUMENTATION_ANOMALY = "instrumentation"
ANOMALY_CLASSES = (PERFORMANCE_ANOMALY, INSTRUMENTATION_ANOMALY)

# --- inference kinds -------------------------------------------------------
CORRELATION = "correlation"
PATTERN = "pattern"
HYPOTHESIS = "hypothesis"
INFERENCE_TYPES = (CORRELATION, PATTERN, HYPOTHESIS)

# --- recommendation outcomes ----------------------------------------------
OUTCOME_PENDING = "pending"
OUTCOME_IMPROVED = "improved"
OUTCOME_WORSENED = "worsened"
OUTCOME_NO_CHANGE = "no_material_change"
OUTCOME_INCONCLUSIVE = "inconclusive"
OUTCOME_CONFOUNDED = "confounded"
OUTCOMES = (OUTCOME_PENDING, OUTCOME_IMPROVED, OUTCOME_WORSENED,
            OUTCOME_NO_CHANGE, OUTCOME_INCONCLUSIVE, OUTCOME_CONFOUNDED)

# --- recommendation lifecycle ---------------------------------------------
STATUS_PROPOSED = "proposed"
STATUS_ACCEPTED = "accepted"
STATUS_IMPLEMENTED = "implemented"
STATUS_REJECTED = "rejected"
STATUS_SUPERSEDED = "superseded"
STATUSES = (STATUS_PROPOSED, STATUS_ACCEPTED, STATUS_IMPLEMENTED,
            STATUS_REJECTED, STATUS_SUPERSEDED)

# --- strategic areas -------------------------------------------------------
AREA_SEO = "seo"
AREA_CONTENT = "content"
AREA_ACQUISITION = "acquisition"
AREA_PAGE_STRUCTURE = "page_structure"
AREA_CONVERSION = "conversion"
AREA_UX = "ux"
AREAS = (AREA_SEO, AREA_CONTENT, AREA_ACQUISITION, AREA_PAGE_STRUCTURE,
         AREA_CONVERSION, AREA_UX)

# Language that asserts causation. The data supports "these moved together",
# never "this made that happen".
_CAUSAL_PATTERNS = re.compile(
    r"\b(caused|causing|causes|drove|driving|led to|leads to|resulted in|"
    r"because of|due to|thanks to|responsible for|explains why|made \w+ (drop|rise|fall))\b",
    re.I,
)


class ModelError(ValueError):
    """A model object violates one of the invariants above."""


def _short_hash(value, length=8):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:length]


def fact_id(source, entity_type, entity_id, metric):
    """Deterministic and stable across runs, so recommendation tracking can
    still resolve the facts that produced a recommendation months later."""
    return f"f_{source}_{entity_type}_{_short_hash(entity_id)}_{metric}"


def inference_id(signal, entity_id):
    return f"i_{signal}_{_short_hash(entity_id)}"


def recommendation_fingerprint(area, entity_id, action_kind):
    """Stable identity for a recommendation across runs.

    The same condition regenerates the same recommendation on every run; the
    fingerprint lets a repeat attach to the existing record as a recurrence
    instead of filling the ledger with duplicates.
    """
    return f"r_{area}_{action_kind}_{_short_hash(entity_id)}"


@dataclass(frozen=True)
class Fact:
    """One measured comparison. Never an opinion."""

    id: str
    source: str
    entity_type: str
    entity_id: str
    metric: str
    period_value: float
    comparison_value: float = None
    delta_abs: float = None
    delta_pct: float = None
    sample_size: float = None
    comparison_sample_size: float = None
    meets_minimum: bool = False
    significant: bool = False
    confidence_interval: tuple = None
    is_final: bool = True
    language: str = None
    period: dict = field(default_factory=dict)
    comparison_period: dict = field(default_factory=dict)
    notes: dict = field(default_factory=dict)

    def to_dict(self):
        data = asdict(self)
        if data.get("confidence_interval") is not None:
            data["confidence_interval"] = list(data["confidence_interval"])
        return data

    @property
    def direction(self):
        if self.delta_abs is None or self.delta_abs == 0:
            return "flat"
        return "up" if self.delta_abs > 0 else "down"


@dataclass(frozen=True)
class Inference:
    """An interpretation of facts. Correlational by construction."""

    id: str
    statement: str
    signal: str
    based_on: tuple
    entity_id: str
    entity_type: str
    type: str = CORRELATION
    confidence: str = MEDIUM
    alternative_explanations: tuple = ()
    causal_claim: bool = False

    def __post_init__(self):
        if not self.based_on:
            raise ModelError(
                f"inference {self.id!r} references no facts. Every interpretation "
                "must be traceable to what was measured."
            )
        if self.type not in INFERENCE_TYPES:
            raise ModelError(f"unknown inference type: {self.type!r}")
        if self.confidence not in CONFIDENCE_LEVELS:
            raise ModelError(f"unknown confidence: {self.confidence!r}")
        if self.causal_claim:
            raise ModelError(
                "causal_claim must be False: this data shows correlation, not causation."
            )
        if not self.alternative_explanations:
            raise ModelError(
                f"inference {self.id!r} lists no alternative explanations. At least "
                "one is required so a reader can see what else could produce it."
            )
        match = _CAUSAL_PATTERNS.search(self.statement)
        if match:
            raise ModelError(
                f"inference {self.id!r} uses causal language ({match.group(0)!r}). "
                "State what moved together, not what made what happen."
            )

    def to_dict(self):
        data = asdict(self)
        data["based_on"] = list(self.based_on)
        data["alternative_explanations"] = list(self.alternative_explanations)
        return data


@dataclass(frozen=True)
class Anomaly:
    """An outlier. Performance anomalies are findings; instrumentation
    anomalies mean the measurement is suspect and suppress recommendations for
    everything they touch."""

    id: str
    anomaly_class: str
    entity_id: str
    entity_type: str
    metric: str
    method: str
    description: str
    score: float = None
    suppresses: tuple = ()

    def __post_init__(self):
        if self.anomaly_class not in ANOMALY_CLASSES:
            raise ModelError(f"unknown anomaly class: {self.anomaly_class!r}")

    @property
    def is_instrumentation(self):
        return self.anomaly_class == INSTRUMENTATION_ANOMALY

    def to_dict(self):
        data = asdict(self)
        data["suppresses"] = list(self.suppresses)
        return data


@dataclass(frozen=True)
class MeasurementPlan:
    """How a recommendation will later be judged.

    Recorded when the recommendation is created, not chosen afterwards — that
    is what stops the system from marking its own homework.
    """

    metric: str
    entity_id: str
    entity_type: str
    direction: str  # "increase" | "decrease"
    min_observation_days: int = 28
    min_sample: float = 0

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Recommendation:
    id: str
    fingerprint: str
    priority: str
    area: str
    action: str
    rationale: str
    supporting_facts: tuple
    measurement_plan: MeasurementPlan
    supporting_inferences: tuple = ()
    confidence: str = MEDIUM
    readiness: str = READY
    status: str = STATUS_PROPOSED
    created_at: str = None
    implemented_at: str = None
    review_after_date: str = None
    outcome: str = OUTCOME_PENDING
    outcome_detail: str = None
    recurrence_count: int = 1

    def __post_init__(self):
        if self.priority not in PRIORITIES:
            raise ModelError(f"unknown priority: {self.priority!r}")
        if self.area not in AREAS:
            raise ModelError(f"unknown area: {self.area!r}")
        if self.readiness not in READINESS_STATES:
            raise ModelError(f"unknown readiness: {self.readiness!r}")
        if self.status not in STATUSES:
            raise ModelError(f"unknown status: {self.status!r}")
        if self.outcome not in OUTCOMES:
            raise ModelError(f"unknown outcome: {self.outcome!r}")
        if not self.supporting_facts:
            raise ModelError(
                f"recommendation {self.id!r} cites no facts. Advice without "
                "measurement behind it is not a recommendation."
            )
        if self.priority in (PRIORITY_HIGH, PRIORITY_MEDIUM) and self.readiness != READY:
            raise ModelError(
                f"recommendation {self.id!r} is {self.priority} but readiness is "
                f"{self.readiness!r}. Anything not ready is Monitor at most."
            )

    def to_dict(self):
        data = asdict(self)
        data["supporting_facts"] = list(self.supporting_facts)
        data["supporting_inferences"] = list(self.supporting_inferences)
        data["measurement_plan"] = self.measurement_plan.to_dict()
        return data


@dataclass
class AnalysisReport:
    """The machine-readable analysis object.

    Sections are *views*: they hold ordered references to facts, inferences and
    recommendations that live once in the flat collections. A finding therefore
    appears once as data and can surface in several sections without the two
    copies drifting apart.
    """

    report_id: str
    generated_at: str
    as_of_date: str
    period: dict
    comparison_periods: list = field(default_factory=list)
    data_coverage: dict = field(default_factory=dict)
    data_quality: dict = field(default_factory=dict)
    facts: list = field(default_factory=list)
    inferences: list = field(default_factory=list)
    anomalies: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    sections: dict = field(default_factory=dict)
    readiness: str = READY
    readiness_note: str = ""

    def fact_by_id(self, fact_ref):
        for fact in self.facts:
            if fact.id == fact_ref:
                return fact
        return None

    def to_dict(self):
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "as_of_date": self.as_of_date,
            "period": self.period,
            "comparison_periods": self.comparison_periods,
            "data_coverage": self.data_coverage,
            "data_quality": self.data_quality,
            "readiness": self.readiness,
            "readiness_note": self.readiness_note,
            "facts": [f.to_dict() for f in self.facts],
            "inferences": [i.to_dict() for i in self.inferences],
            "anomalies": [a.to_dict() for a in self.anomalies],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "sections": self.sections,
        }


def utc_now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
