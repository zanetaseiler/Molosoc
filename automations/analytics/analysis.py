#!/usr/bin/env python3
"""
The Marketing Analysis Agent: what changed, why it matters, what to adjust.

Builds facts from stored history, runs anomaly detection and the named
cross-source signals over them, and assembles the machine-readable report.
Sections are views over the flat collections, so a finding exists once as data
and can appear in several places without the copies drifting.

Read-only throughout. This module never calls an API; it reads the durable
store Phase 1 writes. Clarity in particular comes from the ledger, never from
fresh overlapping API windows.
"""

import datetime as dt
from dataclasses import replace

import anomalies as an
import coverage as cov
import google_hydrate as gh
import history as hist
import periods as pr
import recommend as rc
import signals as sg
import thresholds as th
from analysis_model import (
    AnalysisReport, Fact, INSUFFICIENT_DATA, READY, fact_id, utc_now_iso,
)
from canonical_url import canonicalize
from quality import split_production
from records import CLARITY, GA4, GSC, PAGE, QUERY, SITE, SITE_ENTITY_ID

# Site-level metrics that make up executive health.
EXEC_METRICS = (
    (GA4, "ga4_sessions"), (GA4, "ga4_users"), (GA4, "ga4_views"),
    (GA4, "ga4_engagement_rate"),
    (GA4, hist.PRIMARY_CONVERSION),
    (GA4, "ga4_key_event_begin_checkout"), (GA4, "ga4_key_event_add_to_cart"),
    (GSC, "gsc_clicks"), (GSC, "gsc_impressions"), (GSC, "gsc_ctr"), (GSC, "gsc_position"),
    (CLARITY, "clarity_human_sessions"), (CLARITY, "clarity_sessions"),
    (CLARITY, "clarity_bot_share"), (CLARITY, "clarity_scroll_depth"),
    (CLARITY, "clarity_rage_click_rate"), (CLARITY, "clarity_dead_click_rate"),
    (CLARITY, "clarity_quickback_rate"), (CLARITY, "clarity_script_error_rate"),
)

PAGE_METRICS = (
    (GA4, "ga4_sessions"), (GA4, "ga4_users"), (GA4, "ga4_engagement_rate"),
    (GSC, "gsc_clicks"), (GSC, "gsc_impressions"), (GSC, "gsc_ctr"), (GSC, "gsc_position"),
    (CLARITY, "clarity_visits"), (CLARITY, "clarity_rage_click_rate"),
    (CLARITY, "clarity_dead_click_rate"), (CLARITY, "clarity_quickback_rate"),
)

QUERY_METRICS = (
    (GSC, "gsc_clicks"), (GSC, "gsc_impressions"), (GSC, "gsc_ctr"), (GSC, "gsc_position"),
)


def _build_fact(source, entity_type, entity_id, metric, current, prior, windows):
    """One comparison, with eligibility and significance already decided."""
    if current is None:
        return None

    period_value = current.value
    comparison_value = prior.value if prior else None
    sample = current.sample
    comparison_sample = prior.sample if prior else None

    delta_abs = None if comparison_value is None else period_value - comparison_value
    delta_pct = th.relative_change(period_value, comparison_value) \
        if comparison_value is not None else None

    is_rate = metric.endswith(("_rate", "_share")) or metric == "gsc_ctr"
    is_position = metric == "gsc_position"

    if comparison_value is None:
        significant = False
    elif is_position:
        significant = th.is_significant_position(period_value, comparison_value, sample)
    elif is_rate and sample and comparison_sample:
        significant = th.is_significant_rate(
            period_value * sample, sample,
            comparison_value * comparison_sample, comparison_sample,
        )
    else:
        significant = th.is_significant_count(metric, period_value, comparison_value)

    meets_minimum = _meets_minimum(entity_type, metric, current, prior)
    interval = None
    if is_rate and sample:
        interval = th.proportion_confidence_interval(period_value * sample, sample)

    return Fact(
        id=fact_id(source, entity_type, entity_id, metric),
        source=source, entity_type=entity_type, entity_id=entity_id, metric=metric,
        period_value=period_value, comparison_value=comparison_value,
        delta_abs=delta_abs, delta_pct=delta_pct,
        sample_size=sample, comparison_sample_size=comparison_sample,
        meets_minimum=meets_minimum, significant=significant,
        confidence_interval=interval, is_final=current.is_final,
        language=current.language,
        period=windows[pr.PERIOD].to_dict(),
        comparison_period=windows[pr.PRIOR].to_dict(),
        notes={"dates_present": len(current.dates)},
    )


def _meets_minimum(entity_type, metric, current, prior):
    prior_value = prior.value if prior else 0
    prior_sample = prior.sample if prior else 0

    if entity_type == QUERY:
        if metric in ("gsc_ctr", "gsc_position"):
            return th.query_eligible_for_ctr(current.sample or 0, prior_sample or 0)
        if metric == "gsc_clicks":
            return th.query_eligible_for_click_loss(prior_value or 0)
        return (current.value or 0) >= th.MIN_QUERY_IMPRESSIONS
    if entity_type == PAGE:
        if metric.startswith("clarity_") and metric.endswith("_rate"):
            return th.page_eligible_for_friction(current.sample or 0)
        if metric == "ga4_engagement_rate":
            return th.page_eligible_for_engagement(current.sample or 0, prior_sample or 0)
        return (current.value or 0) >= th.MIN_PAGE_SESSIONS
    if metric.startswith("ga4_key_event_"):
        return th.eligible_for_conversion(current.sample or 0, prior_sample or 0)
    return True


def build_facts(period_records, prior_records, windows, max_entities=25):
    """Every fact the analysis reasons over.

    Non-production pages are excluded first: staging URLs are real rows that
    would otherwise distort every page-level total.
    """
    period_records, excluded = split_production(period_records)
    prior_records, _ = split_production(prior_records)

    facts = []

    def add(source, entity_type, entity_id, metric):
        current = hist.aggregate(period_records, metric, entity_id, entity_type)
        prior = hist.aggregate(prior_records, metric, entity_id, entity_type)
        fact = _build_fact(source, entity_type, entity_id, metric, current, prior, windows)
        if fact is not None:
            facts.append(fact)

    for source, metric in EXEC_METRICS:
        add(source, SITE, SITE_ENTITY_ID, metric)

    pages = hist.entities(period_records, PAGE)[:max_entities]
    for entity_id in pages:
        for source, metric in PAGE_METRICS:
            add(source, PAGE, entity_id, metric)

    queries = hist.entities(period_records, QUERY)[:max_entities]
    for entity_id in queries:
        for source, metric in QUERY_METRICS:
            add(source, QUERY, entity_id, metric)

    return facts, excluded


def _annotate_conversion_boundary(facts, boundary_info):
    """Mark conversion facts whose comparison window predates ecommerce tracking.

    The comparison is already absent in that case — aggregate() returns None for
    a window with no records, so no delta is computed and nothing reads as a
    change from zero. This adds the reason, so a reader sees "not tracked then"
    rather than an unexplained blank.
    """
    if not boundary_info or boundary_info.get("comparison_valid"):
        return facts

    annotated = []
    for fact in facts:
        if not fact.metric.startswith("ga4_key_event_"):
            annotated.append(fact)
            continue
        notes = dict(fact.notes)
        notes["comparison_unavailable_reason"] = (
            "ecommerce tracking was not active for the whole comparison period; "
            "absence of conversion data there is unmeasured, not zero sales"
        )
        notes["ecommerce_tracking_period_state"] = boundary_info.get("period_state")
        notes["ecommerce_tracking_prior_state"] = boundary_info.get("prior_state")
        annotated.append(replace(fact, notes=notes, comparison_value=None,
                                 delta_abs=None, delta_pct=None, significant=False))
    return annotated


def detect_all_anomalies(facts, baseline_records, windows):
    """Performance and instrumentation anomalies over the analysis window."""
    index = sg.FactIndex(facts)
    found = []

    # Instrumentation first: these suppress everything downstream.
    found += an.detect_source_divergence(
        index.value(SITE_ENTITY_ID, "ga4_sessions"),
        index.value(SITE_ENTITY_ID, "clarity_sessions"),
    )
    found += an.detect_bot_share_anomaly(
        index.value(SITE_ENTITY_ID, "clarity_bot_share"),
        index.prior(SITE_ENTITY_ID, "clarity_bot_share"),
    )
    found += an.detect_script_error_spike(
        index.value(SITE_ENTITY_ID, "clarity_script_error_rate"),
        index.prior(SITE_ENTITY_ID, "clarity_script_error_rate"),
    )

    # Performance outliers, from the trailing daily series where one exists.
    for metric in ("clarity_human_sessions", "clarity_sessions"):
        series = hist.daily_series(baseline_records, metric, SITE_ENTITY_ID, SITE)
        if series:
            found += an.detect_outliers({SITE_ENTITY_ID: series}, metric, SITE)
            found += an.detect_collapse_to_zero({SITE_ENTITY_ID: series}, metric, SITE)

    return found


def _strongest_changes(facts):
    """The biggest positive and negative moves that actually cleared the bar."""
    movers = [f for f in facts
              if f.entity_type == SITE and f.significant and f.delta_pct is not None
              and not f.metric.endswith("_share")]
    if not movers:
        return None, None
    ups = [f for f in movers if f.delta_abs > 0]
    downs = [f for f in movers if f.delta_abs < 0]
    strongest_up = max(ups, key=lambda f: abs(f.delta_pct), default=None)
    strongest_down = max(downs, key=lambda f: abs(f.delta_pct), default=None)
    # For position, lower is better — a "rise" is a decline in performance.
    return strongest_up, strongest_down


def build_sections(facts, inferences, recommendations, anomaly_list, index):
    """The eight human-facing views, as ordered references into the flat data."""
    site_facts = [f for f in facts if f.entity_type == SITE]
    strongest_up, strongest_down = _strongest_changes(facts)

    def ids(items):
        return [i.id for i in items]

    traffic = [f for f in site_facts if f.metric in
               ("ga4_sessions", "ga4_users", "ga4_views", "clarity_human_sessions")]
    organic = [f for f in site_facts if f.metric in
               ("gsc_clicks", "gsc_impressions", "gsc_ctr", "gsc_position")]
    engagement = [f for f in site_facts if f.metric in
                  ("ga4_engagement_rate", "clarity_scroll_depth",
                   hist.PRIMARY_CONVERSION) + hist.SUPPORTING_CONVERSIONS]

    weak_ctr = [f for f in facts
                if f.metric == "gsc_ctr" and f.period_value <= th.WEAK_CTR_MAX
                and (f.sample_size or 0) >= th.STRONG_IMPRESSIONS_MIN]
    proximity = [i for i in inferences if i.signal == sg.THRESHOLD_PROXIMITY]
    gaining = [f for f in facts if f.metric == "gsc_impressions"
               and f.entity_type in (PAGE, QUERY) and f.direction == "up" and f.significant]
    losing = [f for f in facts if f.metric == "gsc_clicks"
              and f.entity_type in (PAGE, QUERY) and f.direction == "down" and f.significant]

    page_sessions = [f for f in facts if f.entity_type == PAGE and f.metric == "ga4_sessions"]
    top_entrances = sorted(page_sessions, key=lambda f: -f.period_value)[:5]
    weak_engagement = [f for f in facts
                       if f.entity_type == PAGE and f.metric == "ga4_engagement_rate"
                       and f.period_value < th.WEAK_ENGAGEMENT_MAX and f.meets_minimum]
    hidden = [i for i in inferences if i.signal == sg.HIDDEN_GEM]

    friction = [i for i in inferences if i.signal == sg.FRICTION_AGAINST_INTENT]
    ux_facts = [f for f in facts if f.metric.startswith("clarity_")
                and f.metric.endswith(("_rate", "depth"))]
    recording_review = sorted({i.entity_id for i in friction})

    return {
        "executive_health": {
            "traffic_trend": ids(traffic),
            "organic_search_trend": ids(organic),
            "engagement_conversion_trend": ids(engagement),
            "strongest_positive_change": strongest_up.id if strongest_up else None,
            "strongest_negative_change": strongest_down.id if strongest_down else None,
        },
        "seo_opportunities": {
            "gaining_visibility": ids(gaining),
            "losing_clicks": ids(losing),
            "high_impressions_weak_ctr": ids(weak_ctr),
            "ranking_threshold_opportunities": ids(proximity),
            "content_opportunities": ids(
                [i for i in inferences if i.signal in
                 (sg.HIDDEN_GEM, sg.CAPTURE_UP_SATISFACTION_DOWN)]
            ),
        },
        "landing_pages": {
            "top_entrances": ids(top_entrances),
            "traffic_weak_engagement": ids(weak_engagement),
            "strong_engagement_weak_visibility": ids(hidden),
            "conversion_opportunities": ids(
                [f for f in facts if f.metric.startswith("ga4_key_event_")]
            ),
        },
        "clarity_ux": {
            "friction_findings": ids(friction),
            "ux_metrics": ids(ux_facts),
            "behavioural_anomalies": ids(
                [a for a in anomaly_list if not a.is_instrumentation]
            ),
            "pages_for_recording_review": recording_review,
        },
        "cross_source": {
            "inferences": ids(inferences),
            "by_signal": {name: ids([i for i in inferences if i.signal == name])
                          for name in sg.ALL_SIGNALS},
        },
        "prioritized_actions": ids(recommendations),
        "data_quality": {
            "instrumentation_anomalies": ids(
                [a for a in anomaly_list if a.is_instrumentation]
            ),
            "suppressed_entities": sorted(an.suppressed_entities(anomaly_list)),
        },
    }


def analyse(period_records, prior_records, baseline_records, windows,
            clarity_coverage=None, excluded_records=None, now=None,
            conversion_readiness=None, hydration=None, ecommerce_boundary=None):
    """Build the full analysis object from already-loaded history."""
    now = now or dt.datetime.now(dt.timezone.utc)
    facts, excluded = build_facts(period_records, prior_records, windows)
    excluded = list(excluded) + list(excluded_records or [])

    facts = _annotate_conversion_boundary(facts, ecommerce_boundary)
    anomaly_list = detect_all_anomalies(facts, baseline_records, windows)
    index = sg.FactIndex(facts)

    site_sessions = index.value(SITE_ENTITY_ID, "ga4_sessions")
    if site_sessions is None:
        site_sessions = index.value(SITE_ENTITY_ID, "clarity_human_sessions")
    readiness = th.assess_readiness(site_sessions)

    inferences = sg.evaluate(facts)

    site_totals = {
        metric: index.value(SITE_ENTITY_ID, metric)
        for metric in ("gsc_impressions", "gsc_clicks", "ga4_sessions")
    }
    recommendations = rc.build_all(
        inferences, facts, site_totals, readiness.ready, anomaly_list, now=now,
    )

    sections = build_sections(facts, inferences, recommendations, anomaly_list, index)

    report = AnalysisReport(
        report_id=f"analysis_{windows[pr.PERIOD].end}",
        generated_at=utc_now_iso() if now is None else now.replace(microsecond=0).isoformat(),
        as_of_date=windows[pr.PERIOD].end,
        period=windows[pr.PERIOD].to_dict(),
        comparison_periods=[windows[pr.PRIOR].to_dict(), windows[pr.BASELINE].to_dict()],
        data_coverage={
            "clarity_ledger": clarity_coverage or {},
            "clarity_note": pr.describe_coverage(clarity_coverage or {"days_available": 0}),
            "facts_built": len(facts),
        },
        data_quality={
            "excluded_non_production_records": len(excluded),
            "excluded_hosts": sorted({canonicalize(r.entity_id).host for r in excluded}),
            "suppressed_entities": sorted(an.suppressed_entities(anomaly_list)),
            "instrumentation_anomaly_count": sum(
                1 for a in anomaly_list if a.is_instrumentation
            ),
            "tracking_coverage": cov.coverage_from_facts(index),
            "conversions": conversion_readiness or gh.assess_conversions({}, fetched=False),
            "hydration": hydration or {"used": False},
            "ecommerce_boundary": ecommerce_boundary or {
                "start_date": None, "period_state": gh.TRACKING_UNKNOWN,
                "prior_state": gh.TRACKING_UNKNOWN, "comparison_valid": False,
                "note": gh.describe_boundary(gh.TRACKING_UNKNOWN, gh.TRACKING_UNKNOWN),
            },
        },
        facts=facts, inferences=inferences, anomalies=anomaly_list,
        recommendations=recommendations, sections=sections,
        readiness=READY if readiness.ready else INSUFFICIENT_DATA,
        readiness_note=readiness.reason,
    )
    return report


def load_clarity_history(store, windows):
    """Clarity comes only from the durable ledger.

    Its API cannot return history at all, and consecutive multi-day API windows
    overlap — so a comparison built from live calls would double-count. This is
    the one source that must be read from storage.
    """
    period, _ = hist.load_window(store, CLARITY, windows[pr.PERIOD])
    prior, _ = hist.load_window(store, CLARITY, windows[pr.PRIOR])
    baseline, _ = hist.load_window(store, CLARITY, windows[pr.BASELINE])
    coverage = pr.ledger_coverage(hist.available_dates(store, CLARITY), windows)
    return period, prior, baseline, coverage


def analyse_from_store(store, today=None, period_days=pr.DEFAULT_PERIOD_DAYS, now=None,
                       hydrator=None, ecommerce_tracking_start=None):
    """Analyse using stored Clarity history plus, optionally, hydrated Google data.

    Without a hydrator, every source is read from the store — the pure-storage
    path, which is what the offline fixtures exercise.

    With a hydrator, GA4 and Search Console are fetched for exactly the windows
    being compared and normalized through the same canonicalization, production
    filtering and record model as everything else. They are deliberately not
    persisted: those two sources can reconstruct any past period on demand, so
    storing them daily would be a second collection system earning nothing.
    """
    windows = pr.build_windows(today=today, period_days=period_days)

    period_records, prior_records, baseline_records, coverage = \
        load_clarity_history(store, windows)

    # Classify both windows against the ecommerce tracking boundary before any
    # conversion figure is read. Absence of conversion data before the boundary
    # is tracking unavailability, never zero sales.
    boundary = gh.ecommerce_tracking_start(ecommerce_tracking_start)
    period_state = gh.tracking_state_for_window(windows[pr.PERIOD], boundary)
    prior_state = gh.tracking_state_for_window(windows[pr.PRIOR], boundary)

    conversion_readiness = gh.assess_conversions(
        {}, fetched=False, period_state=period_state, prior_state=prior_state,
        boundary=boundary,
    )
    hydration_note = {"used": False}

    if hydrator is None:
        for source in (GA4, GSC):
            got, _ = hist.load_window(store, source, windows[pr.PERIOD])
            period_records += got
            got, _ = hist.load_window(store, source, windows[pr.PRIOR])
            prior_records += got
            got, _ = hist.load_window(store, source, windows[pr.BASELINE])
            baseline_records += got
    else:
        current = hydrator.hydrate(windows[pr.PERIOD])
        previous = hydrator.hydrate(windows[pr.PRIOR])
        period_records += current.records
        prior_records += previous.records
        conversion_readiness = gh.assess_conversions(
            current.key_events, fetched=current.ok,
            period_state=period_state, prior_state=prior_state, boundary=boundary,
        )
        hydration_note = {
            "used": True,
            "windows": [windows[pr.PERIOD].to_dict(), windows[pr.PRIOR].to_dict()],
            "api_calls_made": hydrator.calls_made,
            "period_records": len(current.records),
            "prior_records": len(previous.records),
            "errors": list(current.errors) + list(previous.errors),
            "persisted": False,
            "note": ("GA4 and Search Console were fetched read-only for the compared "
                     "windows and not persisted. Clarity came from the durable "
                     "ledger, which is the only source that cannot be re-queried."),
        }

    return analyse(period_records, prior_records, baseline_records, windows,
                   clarity_coverage=coverage, now=now,
                   conversion_readiness=conversion_readiness,
                   hydration=hydration_note,
                   ecommerce_boundary={
                       "start_date": boundary.isoformat() if boundary else None,
                       "period_state": period_state,
                       "prior_state": prior_state,
                       "comparison_valid": gh.comparison_is_valid(period_state, prior_state),
                       "note": gh.describe_boundary(period_state, prior_state, boundary),
                   })
