#!/usr/bin/env python3
"""
Reading and aggregating stored history for an analysis window.

Aggregation is not "sum the column". Counts sum; rates must be recomputed from
their parts; positions are impression-weighted. Averaging a column of CTRs
across pages is one of the most common ways an analytics report ends up
confidently wrong, so the aggregation rule is declared per metric and applied
here rather than left to each caller.

Clarity is read from the durable ledger only. Its API cannot return history,
and consecutive multi-day API windows overlap — so a comparison built from
fresh API calls would double-count. records.sum_metric enforces that
independently: anything with window_days > 1 is refused.
"""

from collections import defaultdict

from records import MetricRecord, RecordError, sum_metric
from storage import StorageError, facts_key

# --- aggregation rules -----------------------------------------------------
SUM = "sum"
RATIO = "ratio"                  # recomputed from numerator / denominator
WEIGHTED_MEAN = "weighted_mean"  # weighted by each record's sample_basis

AGGREGATION = {
    # Search Console
    "gsc_clicks": (SUM, None),
    "gsc_impressions": (SUM, None),
    "gsc_ctr": (RATIO, ("gsc_clicks", "gsc_impressions")),
    "gsc_position": (WEIGHTED_MEAN, None),
    # GA4
    "ga4_sessions": (SUM, None),
    "ga4_users": (SUM, None),
    "ga4_views": (SUM, None),
    "ga4_engaged_sessions": (SUM, None),
    "ga4_engagement_rate": (RATIO, ("ga4_engaged_sessions", "ga4_sessions")),
    "ga4_key_event_purchase": (SUM, None),
    "ga4_key_event_begin_checkout": (SUM, None),
    "ga4_key_event_add_to_cart": (SUM, None),
    # Clarity
    "clarity_sessions": (SUM, None),
    "clarity_human_sessions": (SUM, None),
    "clarity_bot_sessions": (SUM, None),
    "clarity_distinct_users": (SUM, None),
    "clarity_visits": (SUM, None),
    "clarity_bot_share": (RATIO, ("clarity_bot_sessions", "clarity_sessions")),
    "clarity_scroll_depth": (WEIGHTED_MEAN, None),
    "clarity_pages_per_session": (WEIGHTED_MEAN, None),
    "clarity_total_time": (SUM, None),
    "clarity_active_time": (SUM, None),
}

# Conversion metrics, in the approved hierarchy.
PRIMARY_CONVERSION = "ga4_key_event_purchase"
SUPPORTING_CONVERSIONS = ("ga4_key_event_begin_checkout", "ga4_key_event_add_to_cart")


def aggregation_rule(metric):
    if metric in AGGREGATION:
        return AGGREGATION[metric]
    if metric.endswith(("_rate", "_share")):
        return (WEIGHTED_MEAN, None)
    if metric.endswith("_count"):
        return (SUM, None)
    return (SUM, None)


class Aggregate:
    """An aggregated metric plus the evidence behind it."""

    __slots__ = ("metric", "entity_id", "entity_type", "value", "sample",
                 "dates", "is_final", "language", "record_count")

    def __init__(self, metric, entity_id, entity_type, value, sample, dates,
                 is_final=True, language=None, record_count=0):
        self.metric = metric
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.value = value
        self.sample = sample
        self.dates = dates
        self.is_final = is_final
        self.language = language
        self.record_count = record_count

    def __repr__(self):
        return f"Aggregate({self.metric}, {self.entity_id}, {self.value})"


def load_window(store, source, window, missing_ok=True):
    """Read every stored fact record for a source across a window.

    Missing days are normal — collection starts when it starts, and a gap is
    reported as coverage rather than treated as a zero.
    """
    records, found_dates = [], []
    for date in window.dates():
        try:
            document = store.get_json(facts_key(source, date))
        except StorageError:
            if missing_ok:
                continue
            raise
        found_dates.append(date)
        for row in document.get("records", []):
            records.append(MetricRecord.from_dict(row))
    return records, found_dates


def available_dates(store, source):
    """Every date the store holds facts for, from the key layout."""
    prefix = f"facts/{source}/"
    dates = []
    for key in store.list_keys(prefix):
        name = key[len(prefix):]
        if name.endswith(".json") and not name.endswith(".quality.json"):
            dates.append(name[:-len(".json")])
    return sorted(dates)


def _select(records, metric, entity_id=None, entity_type=None):
    return [r for r in records
            if r.metric == metric
            and (entity_id is None or r.entity_id == entity_id)
            and (entity_type is None or r.entity_type == entity_type)]


def _sum_safely(rows):
    """Sum, refusing anything that would double-count.

    Single-day records sum normally. A single record already covering the whole
    window (as GA4/Search Console emit) is used as-is. A mix, or several
    overlapping multi-day records, is refused rather than guessed at.
    """
    if not rows:
        return None, 0
    if all(r.window_days == 1 for r in rows):
        return sum_metric(rows), len(rows)
    if len(rows) == 1:
        return rows[0].value, 1
    raise RecordError(
        f"refusing to aggregate {rows[0].metric!r}: {len(rows)} records with "
        "window_days > 1 would overlap. Only single-day snapshots may be summed."
    )


def aggregate(records, metric, entity_id=None, entity_type=None):
    """Aggregate one metric over a set of records, by its declared rule."""
    rule, parts = aggregation_rule(metric)
    rows = _select(records, metric, entity_id, entity_type)

    if rule == RATIO:
        # Recompute from the parts first. A ratio is usually *not* stored as
        # its own record — CTR and bot share exist only as clicks/impressions
        # and bots/sessions — and recomputing is the only correct way to
        # aggregate one across days regardless.
        numerator_metric, denominator_metric = parts
        numerator_rows = _select(records, numerator_metric, entity_id, entity_type)
        denominator_rows = _select(records, denominator_metric, entity_id, entity_type)
        numerator, _ = _sum_safely(numerator_rows)
        denominator, _ = _sum_safely(denominator_rows)
        if numerator is not None and denominator:
            source_rows = numerator_rows + denominator_rows
            return Aggregate(
                metric, entity_id, entity_type, numerator / denominator, denominator,
                sorted({r.date for r in source_rows}),
                all(r.is_final for r in source_rows),
                next((r.language for r in source_rows if r.language), None),
                len(source_rows),
            )
        # Fall back to a stored rate only for a single window — averaging
        # stored rates across days is exactly the error this rule prevents.
        if len(rows) == 1:
            return Aggregate(metric, entity_id, entity_type, rows[0].value,
                             rows[0].sample_basis, [rows[0].date], rows[0].is_final,
                             rows[0].language, 1)
        if not rows:
            return None

    if not rows:
        return None

    dates = sorted({r.date for r in rows})
    is_final = all(r.is_final for r in rows)
    language = next((r.language for r in rows if r.language), None)

    if rule == WEIGHTED_MEAN:
        weighted, weight_total = 0.0, 0.0
        for row in rows:
            weight = row.sample_basis if row.sample_basis else 0
            weighted += row.value * weight
            weight_total += weight
        if weight_total:
            return Aggregate(metric, entity_id, entity_type, weighted / weight_total,
                             weight_total, dates, is_final, language, len(rows))
        # No weights recorded: an unweighted mean is the honest fallback, and
        # only defensible because every record covers an equal-length window.
        value = sum(r.value for r in rows) / len(rows)
        return Aggregate(metric, entity_id, entity_type, value, None, dates,
                         is_final, language, len(rows))

    total, count = _sum_safely(rows)
    if total is None:
        return None
    basis = sum(r.sample_basis for r in rows if r.sample_basis) or None
    return Aggregate(metric, entity_id, entity_type, total, basis, dates,
                     is_final, language, count)


def entities(records, entity_type, metric=None):
    """Distinct entity ids of a type, optionally restricted to one metric."""
    return sorted({r.entity_id for r in records
                   if r.entity_type == entity_type
                   and (metric is None or r.metric == metric)})


def daily_series(records, metric, entity_id=None, entity_type=None):
    """date -> value, for anomaly detection over a trailing window."""
    series = defaultdict(float)
    for row in _select(records, metric, entity_id, entity_type):
        if row.window_days == 1:
            series[row.date] += row.value
    return dict(sorted(series.items()))


def language_of(records, entity_id):
    for row in records:
        if row.entity_id == entity_id and row.language:
            return row.language
    return None
