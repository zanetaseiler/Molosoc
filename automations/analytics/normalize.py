#!/usr/bin/env python3
"""
Convert each source's raw payload into the shared MetricRecord schema.

Nothing here talks to a network. These functions take the payloads the
verified read-only clients already return and reshape them, which keeps the
whole normalization layer testable offline against captured fixtures.

Two things this layer is responsible for:

* Canonical page identity. GA4 reports paths, Search Console reports absolute
  URLs, Clarity reports whatever the browser saw. All three become one
  canonical URL here, or nothing downstream can join them.
* Metric classification. Bot counts, bot share and script-error rates are
  data-quality metrics, not performance metrics, and are labelled as such at
  the point of creation rather than being sorted out later.

A note on Clarity's window: numOfDays=1 means "the trailing 24 hours from now",
not "the calendar day". A snapshot is therefore stamped with the UTC date it
was collected on and the exact instant its window ends. One snapshot per UTC
date keeps the daily buckets non-overlapping; the collector enforces that.
"""

import datetime as dt

from analytics_common import as_number
from canonical_url import canonicalize, detect_language
from records import (
    CLARITY, COUNTRY, DATA_QUALITY, DEVICE, GA4, GSC, OPERATING_SYSTEM, PAGE,
    PAGE_TITLE, PERFORMANCE, QUERY, REFERRER, SITE, SITE_ENTITY_ID, BROWSER,
    MetricRecord,
)

# Clarity friction metrics: metricName -> (record metric name, class).
# Script errors are classified as data quality: the design treats a script
# error spike as an instrumentation signal (a deploy regression breaking
# measurement) rather than a user-behaviour trend.
CLARITY_FRICTION = {
    "DeadClickCount": ("clarity_dead_click", PERFORMANCE),
    "RageClickCount": ("clarity_rage_click", PERFORMANCE),
    "QuickbackClick": ("clarity_quickback", PERFORMANCE),
    "ExcessiveScroll": ("clarity_excessive_scroll", PERFORMANCE),
    "ErrorClickCount": ("clarity_error_click", PERFORMANCE),
    "ScriptErrorCount": ("clarity_script_error", DATA_QUALITY),
}

# Clarity dimension metrics: metricName -> (entity_type, record metric name).
CLARITY_DIMENSIONS = {
    "Browser": (BROWSER, "clarity_sessions"),
    "Device": (DEVICE, "clarity_sessions"),
    "OS": (OPERATING_SYSTEM, "clarity_sessions"),
    "Country": (COUNTRY, "clarity_sessions"),
    "PageTitle": (PAGE_TITLE, "clarity_sessions"),
    "ReferrerUrl": (REFERRER, "clarity_sessions"),
}

DIRECT_REFERRER = "(direct)"

# Conversion events, per the approved definitions. purchase is the headline
# business conversion; the other two are supporting funnel steps recorded when
# GA4 reports them. Each is its own metric — never a single blended "conversions"
# figure, which would make the funnel unreadable.
HEADLINE_CONVERSION = "purchase"
SUPPORTING_FUNNEL_EVENTS = ("begin_checkout", "add_to_cart")
TRACKED_KEY_EVENTS = (HEADLINE_CONVERSION,) + SUPPORTING_FUNNEL_EVENTS


def merge_by_canonical_page(rows, url_key, count_fields=(), rate_fields=(),
                            weight_field=None):
    """Collapse source rows that resolve to the same canonical page.

    GA4's landing-page report really does return `/`, `/?fbclid=…` and a second
    `fbclid` variant as three rows for one page — that was in the very first
    verified run. Canonicalization gives them one identity, so their counts must
    be added rather than emitted as three records for the same page, which would
    both overstate nothing and trip the aggregation guard downstream.

    `count_fields` are summed. `rate_fields` are recomputed as a weighted mean
    over `weight_field` (impressions, for CTR and position) rather than averaged.
    """
    merged = {}
    order = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        canonical, language, source, notes = page_context(row.get(url_key, ""))
        key = canonical.url
        if key not in merged:
            merged[key] = {
                "canonical": canonical, "language": language,
                "language_source": source, "notes": notes,
                "counts": {f: 0 for f in count_fields},
                "weighted": {f: 0.0 for f in rate_fields},
                "weight": 0.0, "source_rows": 0,
            }
            order.append(key)
        entry = merged[key]
        entry["source_rows"] += 1
        for field in count_fields:
            entry["counts"][field] += as_number(row.get(field, 0))
        weight = as_number(row.get(weight_field, 0)) if weight_field else 0
        entry["weight"] += weight
        for field in rate_fields:
            entry["weighted"][field] += float(row.get(field, 0) or 0) * weight
        # Keep every original URL that folded into this identity, and every
        # tracking parameter dropped along the way — the merge must stay
        # auditable, not just correct.
        originals = entry["notes"].setdefault("merged_from", [])
        if canonical.original and canonical.original not in originals:
            originals.append(canonical.original)
        if canonical.dropped_params:
            dropped = entry["notes"].setdefault("dropped_params", [])
            for name in canonical.dropped_params:
                if name not in dropped:
                    dropped.append(name)

    for key in order:
        entry = merged[key]
        rates = {}
        for field in rate_fields:
            rates[field] = (entry["weighted"][field] / entry["weight"]
                            if entry["weight"] else 0.0)
        if entry["source_rows"] < 2:
            entry["notes"].pop("merged_from", None)
        yield entry["canonical"], entry["language"], entry["language_source"], \
            entry["notes"], entry["counts"], rates, entry["weight"]


def page_context(url):
    """Canonical identity plus the language metadata every page record carries."""
    canonical = canonicalize(url)
    language, source = detect_language(canonical)
    notes = {
        "host_classification": canonical.classification,
        "original_url": canonical.original,
        # The full path is preserved so language can be re-derived later
        # without re-collecting anything.
        "path": canonical.path,
    }
    if canonical.dropped_params:
        notes["dropped_params"] = canonical.dropped_params
    return canonical, language, source, notes


def _rows(entry):
    rows = entry.get("information") or []
    return rows if isinstance(rows, list) else [rows]


def _as_metric_list(payload):
    """Clarity returns a list of metric objects; some responses wrap it."""
    if isinstance(payload, dict):
        payload = next((v for v in payload.values() if isinstance(v, list)), [payload])
    if not isinstance(payload, list):
        raise ValueError(
            f"expected a list of Clarity metrics, got {type(payload).__name__}"
        )
    return [entry for entry in payload if isinstance(entry, dict)]


def clarity_records(payload, date, collected_at, window_end=None, num_days=1):
    """Normalize one Clarity Live Insights payload into MetricRecords.

    `num_days` is carried through to window_days so the aggregation guard in
    records.sum_metric can refuse to sum overlapping multi-day snapshots.
    """
    window_end = window_end or collected_at
    out = []

    def add(entity_type, entity_id, metric, value, metric_class=PERFORMANCE,
            sample_basis=None, raw=None, notes=None, language=None,
            language_source=None):
        out.append(MetricRecord(
            date=date, source=CLARITY, entity_type=entity_type, entity_id=entity_id,
            metric=metric, value=value, metric_class=metric_class,
            sample_basis=sample_basis, window_days=num_days,
            collected_at=collected_at, window_end=window_end,
            is_final=True,  # Clarity live insights are not revised
            raw_value=raw, language=language, language_source=language_source,
            notes=notes or {},
        ))

    for entry in _as_metric_list(payload):
        name = str(entry.get("metricName", ""))
        rows = _rows(entry)
        first = rows[0] if rows and isinstance(rows[0], dict) else {}

        if name == "Traffic" and first:
            total = as_number(first.get("totalSessionCount", 0))
            bots = as_number(first.get("totalBotSessionCount", 0))
            add(SITE, SITE_ENTITY_ID, "clarity_sessions", total,
                raw=first.get("totalSessionCount"))
            add(SITE, SITE_ENTITY_ID, "clarity_bot_sessions", bots, DATA_QUALITY,
                sample_basis=total, raw=first.get("totalBotSessionCount"))
            # Human sessions is what a traffic trend should read, not the total.
            add(SITE, SITE_ENTITY_ID, "clarity_human_sessions", max(0, total - bots),
                sample_basis=total)
            add(SITE, SITE_ENTITY_ID, "clarity_bot_share",
                (bots / total) if total else 0.0, DATA_QUALITY, sample_basis=total)
            add(SITE, SITE_ENTITY_ID, "clarity_distinct_users",
                as_number(first.get("distinctUserCount", 0)),
                raw=first.get("distinctUserCount"))
            add(SITE, SITE_ENTITY_ID, "clarity_pages_per_session",
                as_number(first.get("pagesPerSessionPercentage", 0)),
                sample_basis=total)

        elif name == "EngagementTime" and first:
            add(SITE, SITE_ENTITY_ID, "clarity_total_time",
                as_number(first.get("totalTime", 0)), raw=first.get("totalTime"))
            add(SITE, SITE_ENTITY_ID, "clarity_active_time",
                as_number(first.get("activeTime", 0)), raw=first.get("activeTime"))

        elif name == "ScrollDepth" and first:
            add(SITE, SITE_ENTITY_ID, "clarity_scroll_depth",
                as_number(first.get("averageScrollDepth", 0)))

        elif name in CLARITY_FRICTION:
            metric, metric_class = CLARITY_FRICTION[name]
            for row in rows:
                if not isinstance(row, dict):
                    continue
                basis = as_number(row.get("sessionsCount", 0))
                add(SITE, SITE_ENTITY_ID, f"{metric}_rate",
                    as_number(row.get("sessionsWithMetricPercentage", 0)) / 100.0,
                    metric_class, sample_basis=basis,
                    raw=row.get("sessionsWithMetricPercentage"))
                add(SITE, SITE_ENTITY_ID, f"{metric}_count",
                    as_number(row.get("subTotal", 0)), metric_class,
                    sample_basis=basis, raw=row.get("subTotal"))
                break  # site-level friction has one row unless dimensioned

        elif name == "PopularPages":
            normalized = [{"url": r.get("url") or r.get("name") or "",
                           "visits": as_number(r.get("visitsCount",
                                                     r.get("sessionsCount", 0)))}
                          for r in rows if isinstance(r, dict)]
            for canonical, language, lang_source, notes, counts, _rates, _weight in \
                    merge_by_canonical_page(normalized, "url",
                                            count_fields=("visits",)):
                add(PAGE, canonical.url, "clarity_visits", counts["visits"],
                    notes=notes, language=language, language_source=lang_source)

        elif name in CLARITY_DIMENSIONS:
            entity_type, metric = CLARITY_DIMENSIONS[name]
            for row in rows:
                if not isinstance(row, dict):
                    continue
                label = str(row.get("name", "")).strip()
                if entity_type == REFERRER and label.lower() in ("none", ""):
                    label = DIRECT_REFERRER
                if not label:
                    continue
                add(entity_type, label, metric,
                    as_number(row.get("sessionsCount", 0)), raw=row.get("sessionsCount"))

    return out


def _window_days(date_range):
    start = dt.date.fromisoformat(date_range["start"])
    end = dt.date.fromisoformat(date_range["end"])
    return (end - start).days + 1


def _is_final(end_date, collected_at, revision_days=3):
    """Google revises recent days; treat anything inside the revision window as
    provisional so a report can say so instead of showing a phantom dip."""
    try:
        collected = dt.date.fromisoformat(str(collected_at)[:10])
    except ValueError:
        return False
    return dt.date.fromisoformat(end_date) <= collected - dt.timedelta(days=revision_days)


def ga4_records(result, collected_at):
    """Normalize the GA4 check result (google_connection_test.check_ga4)."""
    if not result.get("ok"):
        return []

    window = result["dateRange"]
    date, days = window["end"], _window_days(window)
    final = _is_final(window["end"], collected_at)
    out = []

    def add(entity_type, entity_id, metric, value, sample_basis=None, notes=None,
            language=None, language_source=None):
        out.append(MetricRecord(
            date=date, source=GA4, entity_type=entity_type, entity_id=entity_id,
            metric=metric, value=value, metric_class=PERFORMANCE,
            sample_basis=sample_basis, window_days=days, collected_at=collected_at,
            window_end=window["end"], is_final=final, language=language,
            language_source=language_source, notes=notes or {},
        ))

    add(SITE, SITE_ENTITY_ID, "ga4_users", as_number(result.get("users", 0)))
    add(SITE, SITE_ENTITY_ID, "ga4_sessions", as_number(result.get("sessions", 0)))
    add(SITE, SITE_ENTITY_ID, "ga4_views", as_number(result.get("views", 0)))

    for canonical, language, lang_source, notes, counts, _rates, _weight in \
            merge_by_canonical_page(result.get("landingPages", []), "landingPage",
                                    count_fields=("sessions", "activeUsers")):
        add(PAGE, canonical.url, "ga4_sessions", counts["sessions"],
            notes=notes, language=language, language_source=lang_source)
        add(PAGE, canonical.url, "ga4_users", counts["activeUsers"],
            notes=notes, language=language, language_source=lang_source)

    # Key events, when the payload carries them. purchase is the headline
    # business conversion; begin_checkout and add_to_cart are the supporting
    # funnel steps. Each stays its own metric so the funnel remains readable.
    key_events = result.get("keyEvents") or {}
    sessions = as_number(result.get("sessions", 0))
    for event_name in TRACKED_KEY_EVENTS:
        if event_name not in key_events:
            continue
        add(SITE, SITE_ENTITY_ID, f"ga4_key_event_{event_name}",
            as_number(key_events[event_name]), sample_basis=sessions)

    return out


def gsc_records(result, collected_at):
    """Normalize the Search Console check result
    (google_connection_test.check_search_console)."""
    if not result.get("ok"):
        return []

    window = result["dateRange"]
    date, days = window["end"], _window_days(window)
    final = _is_final(window["end"], collected_at)
    out = []

    def add(entity_type, entity_id, metric, value, sample_basis=None, notes=None,
            language=None, language_source=None):
        out.append(MetricRecord(
            date=date, source=GSC, entity_type=entity_type, entity_id=entity_id,
            metric=metric, value=value, metric_class=PERFORMANCE,
            sample_basis=sample_basis, window_days=days, collected_at=collected_at,
            window_end=window["end"], is_final=final, language=language,
            language_source=language_source, notes=notes or {},
        ))

    impressions = as_number(result.get("impressions", 0))
    add(SITE, SITE_ENTITY_ID, "gsc_clicks", as_number(result.get("clicks", 0)))
    add(SITE, SITE_ENTITY_ID, "gsc_impressions", impressions)
    # CTR and position are rates: they carry their denominator so significance
    # can be computed later, and so they are never averaged across rows.
    add(SITE, SITE_ENTITY_ID, "gsc_ctr", float(result.get("ctr", 0.0)),
        sample_basis=impressions)
    add(SITE, SITE_ENTITY_ID, "gsc_position", float(result.get("position", 0.0)),
        sample_basis=impressions)

    for row in result.get("topQueries", []):
        query = str(row.get("query", "")).strip()
        if not query:
            continue
        row_impressions = as_number(row.get("impressions", 0))
        add(QUERY, query, "gsc_clicks", as_number(row.get("clicks", 0)))
        add(QUERY, query, "gsc_impressions", row_impressions)
        add(QUERY, query, "gsc_ctr", float(row.get("ctr", 0.0)), sample_basis=row_impressions)
        add(QUERY, query, "gsc_position", float(row.get("position", 0.0)),
            sample_basis=row_impressions)

    for canonical, language, lang_source, notes, counts, rates, impressions in \
            merge_by_canonical_page(result.get("topPages", []), "page",
                                    count_fields=("clicks", "impressions"),
                                    rate_fields=("ctr", "position"),
                                    weight_field="impressions"):
        lang = {"language": language, "language_source": lang_source}
        add(PAGE, canonical.url, "gsc_clicks", counts["clicks"], notes=notes, **lang)
        add(PAGE, canonical.url, "gsc_impressions", counts["impressions"],
            notes=notes, **lang)
        add(PAGE, canonical.url, "gsc_ctr", rates["ctr"],
            sample_basis=impressions, notes=notes, **lang)
        add(PAGE, canonical.url, "gsc_position", rates["position"],
            sample_basis=impressions, notes=notes, **lang)

    return out
