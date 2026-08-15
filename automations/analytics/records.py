#!/usr/bin/env python3
"""
The normalized historical record every source is stored as.

One row per date x source x entity x metric. The long format is deliberate:
Clarity's metric set varies by project and by what data exists, and GA4/Search
Console dimensions will grow over time. A wide table would need a migration for
each; this one absorbs new metrics as data.

Two invariants are enforced here rather than left to convention:

1. Performance metrics and data-quality metrics are different classes and are
   never mixed. A bot-share figure must never be summed into a traffic trend.
2. Only window_days == 1 records may be aggregated across dates. Clarity's API
   can return 1-, 2- or 3-day windows; consecutive multi-day windows overlap,
   so summing them double-counts. sum_metric() refuses rather than trusting the
   caller to remember.
"""

import datetime as dt
from dataclasses import dataclass, asdict, field

# --- metric classes --------------------------------------------------------
PERFORMANCE = "performance"
DATA_QUALITY = "data_quality"
METRIC_CLASSES = (PERFORMANCE, DATA_QUALITY)

# --- sources ---------------------------------------------------------------
GA4 = "ga4"
GSC = "gsc"
CLARITY = "clarity"
SOURCES = (GA4, GSC, CLARITY)

# --- entity types ----------------------------------------------------------
SITE = "site"
PAGE = "page"
QUERY = "query"
BROWSER = "browser"
DEVICE = "device"
OPERATING_SYSTEM = "os"
COUNTRY = "country"
REFERRER = "referrer"
PAGE_TITLE = "page_title"
ENTITY_TYPES = (
    SITE, PAGE, QUERY, BROWSER, DEVICE, OPERATING_SYSTEM, COUNTRY, REFERRER, PAGE_TITLE,
)

SITE_ENTITY_ID = "site"


class RecordError(ValueError):
    """A record violates one of the invariants above."""


@dataclass(frozen=True)
class MetricRecord:
    """One measurement, normalized across all three sources.

    date          UTC date the measurement describes (YYYY-MM-DD).
    window_days   Length of the window the value covers, ending on `date`.
                  1 for every daily record. Only 1 may be aggregated.
    entity_id     Canonical identity: a canonical URL for pages, the query
                  string for queries, "site" for site-wide totals.
    sample_basis  Denominator behind a rate (e.g. the session count behind a
                  friction percentage). Required for rates so significance can
                  be computed later without re-deriving it.
    raw_value     The value exactly as the API returned it, before any
                  coercion, so a parsing change can be audited against source.
    is_final      False while the source may still revise the figure.
    """

    date: str
    source: str
    entity_type: str
    entity_id: str
    metric: str
    value: float
    metric_class: str = PERFORMANCE
    sample_basis: float = None
    window_days: int = 1
    collected_at: str = None
    window_end: str = None
    is_final: bool = True
    raw_value: object = None
    #: Language of the page ("cs", "en", "und"), and how it was determined.
    #: Preserved on every page record so CZ/EN can be segmented later; reporting
    #: is not split by language yet, but the history will support it when volume
    #: justifies it. "und" is a legitimate value on a site whose two languages
    #: share a URL root — the full path is kept so it can be back-filled.
    language: str = None
    language_source: str = None
    notes: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.source not in SOURCES:
            raise RecordError(f"unknown source: {self.source!r}")
        if self.entity_type not in ENTITY_TYPES:
            raise RecordError(f"unknown entity_type: {self.entity_type!r}")
        if self.metric_class not in METRIC_CLASSES:
            raise RecordError(f"unknown metric_class: {self.metric_class!r}")
        if self.window_days < 1:
            raise RecordError(f"window_days must be >= 1, got {self.window_days}")
        try:
            dt.date.fromisoformat(self.date)
        except (TypeError, ValueError):
            raise RecordError(f"date must be YYYY-MM-DD, got {self.date!r}") from None
        if not self.entity_id:
            raise RecordError("entity_id must not be empty")

    @property
    def is_aggregatable(self):
        """Only single-day windows can be summed across dates without
        double-counting. See the module docstring."""
        return self.window_days == 1

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        allowed = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in allowed})


def sum_metric(records, metric=None):
    """Sum a metric across dates, refusing anything that would double-count.

    Raises rather than silently producing an inflated number: an overlapping
    multi-day Clarity window summed with its neighbours is the single easiest
    way to corrupt the whole history, and it produces a plausible-looking
    figure that nobody catches.
    """
    selected = [r for r in records if metric is None or r.metric == metric]
    overlapping = [r for r in selected if not r.is_aggregatable]
    if overlapping:
        offender = overlapping[0]
        raise RecordError(
            f"refusing to aggregate {offender.metric!r}: "
            f"{len(overlapping)} record(s) have window_days > 1 and overlap "
            "their neighbours. Only single-day snapshots may be summed."
        )

    classes = {r.metric_class for r in selected}
    if len(classes) > 1:
        raise RecordError(
            f"refusing to aggregate across metric classes {sorted(classes)}: "
            "performance and data-quality metrics are not comparable."
        )

    seen = set()
    for record in selected:
        key = (record.date, record.source, record.entity_type, record.entity_id, record.metric)
        if key in seen:
            raise RecordError(
                f"refusing to aggregate: duplicate record for {key}. "
                "Each date/entity/metric must appear once."
            )
        seen.add(key)

    return sum(r.value for r in selected)


def performance_only(records):
    """Drop data-quality records. Use before anything that reads as a trend."""
    return [r for r in records if r.metric_class == PERFORMANCE]


def data_quality_only(records):
    return [r for r in records if r.metric_class == DATA_QUALITY]


def utc_now_iso():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def utc_today():
    return dt.datetime.now(dt.timezone.utc).date().isoformat()
