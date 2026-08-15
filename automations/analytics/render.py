#!/usr/bin/env python3
"""
Human-readable rendering of an AnalysisReport.

The JSON object is the contract; this is the view. Nothing is computed here —
every number and claim already exists in the report, so the prose and the data
cannot drift apart.

The renderer keeps facts and inferences visibly separate, because that
distinction is the point of the whole model and it would be trivially lost in
a paragraph that reads well.
"""

from analysis_model import (
    INSUFFICIENT_DATA, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_MONITOR,
)
import history as hist

_RATE_METRICS = ("_rate", "_share", "gsc_ctr", "engagement_rate")

METRIC_LABELS = {
    "ga4_sessions": "Sessions (GA4)",
    "ga4_users": "Users (GA4)",
    "ga4_views": "Views (GA4)",
    "ga4_engagement_rate": "Engagement rate",
    "ga4_key_event_purchase": "Purchases",
    "ga4_key_event_begin_checkout": "Checkouts started",
    "ga4_key_event_add_to_cart": "Add to cart",
    "gsc_clicks": "Search clicks",
    "gsc_impressions": "Search impressions",
    "gsc_ctr": "Search CTR",
    "gsc_position": "Average position",
    "clarity_sessions": "Clarity sessions (incl. bots)",
    "clarity_human_sessions": "Clarity sessions (bot-adjusted)",
    "clarity_bot_share": "Bot share",
    "clarity_scroll_depth": "Average scroll depth",
    "clarity_rage_click_rate": "Rage clicks",
    "clarity_dead_click_rate": "Dead clicks",
    "clarity_quickback_rate": "Quick-backs",
    "clarity_script_error_rate": "Script errors",
    "clarity_visits": "Clarity visits",
}


def label(metric):
    return METRIC_LABELS.get(metric, metric)


def is_rate(metric):
    return any(marker in metric for marker in _RATE_METRICS)


def format_value(metric, value):
    if value is None:
        return "—"
    if metric == "gsc_position":
        return f"{value:.1f}"
    if metric == "clarity_scroll_depth":
        return f"{value:.1f}%"
    if is_rate(metric):
        return f"{value:.2%}"
    return f"{value:,.0f}"


def format_change(fact):
    if fact.comparison_value is None:
        return "no comparison"
    if fact.delta_abs == 0:
        return "unchanged"
    arrow = "+" if fact.delta_abs > 0 else ""
    if fact.delta_pct is None:
        return f"{arrow}{format_value(fact.metric, fact.delta_abs)}"
    marker = "" if fact.significant else " (not significant)"
    return f"{arrow}{fact.delta_pct:.0%}{marker}"


def _fact_line(fact):
    return (f"- **{label(fact.metric)}**: {format_value(fact.metric, fact.period_value)} "
            f"(was {format_value(fact.metric, fact.comparison_value)}, "
            f"{format_change(fact)}) `{fact.id}`")


def _resolve(report, ids):
    lookup = {f.id: f for f in report.facts}
    return [lookup[i] for i in ids if i in lookup]


def _inference_lookup(report):
    return {i.id: i for i in report.inferences}


def render_markdown(report):
    """The eight required sections, in reading order."""
    out = []
    add = out.append

    period = report.period
    add(f"# Molosoc marketing analysis — {report.as_of_date}")
    add("")
    add(f"Period **{period['start']} to {period['end']}** ({period['days']} days), "
        f"compared against {report.comparison_periods[0]['start']} to "
        f"{report.comparison_periods[0]['end']}.")
    add("")

    # 1. Executive summary
    add("## Executive summary")
    add("")
    if report.readiness == INSUFFICIENT_DATA:
        add(f"> **Insufficient data for recommendation.** {report.readiness_note}")
        add("")
        add("Everything below is reported as measured. No actions are proposed above "
            "Monitor until volume supports them.")
        add("")
    exec_section = report.sections.get("executive_health", {})
    strongest_up = report.fact_by_id(exec_section.get("strongest_positive_change"))
    strongest_down = report.fact_by_id(exec_section.get("strongest_negative_change"))
    if strongest_up:
        add(f"- Strongest positive change: **{label(strongest_up.metric)}** "
            f"{format_change(strongest_up)} "
            f"({format_value(strongest_up.metric, strongest_up.comparison_value)} → "
            f"{format_value(strongest_up.metric, strongest_up.period_value)})")
    if strongest_down:
        add(f"- Strongest negative change: **{label(strongest_down.metric)}** "
            f"{format_change(strongest_down)} "
            f"({format_value(strongest_down.metric, strongest_down.comparison_value)} → "
            f"{format_value(strongest_down.metric, strongest_down.period_value)})")
    if not (strongest_up or strongest_down):
        add("- No site-level change cleared the significance thresholds this period.")
    counts = _priority_counts(report)
    add(f"- Recommendations: {counts[PRIORITY_HIGH]} High, {counts[PRIORITY_MEDIUM]} Medium, "
        f"{counts[PRIORITY_MONITOR]} Monitor")
    add("")

    # 2. What changed
    add("## What changed")
    add("")
    add("*Measured facts. Every line is a number, not an interpretation.*")
    add("")
    for title, key in (("Traffic", "traffic_trend"),
                       ("Organic search", "organic_search_trend"),
                       ("Engagement and conversion", "engagement_conversion_trend")):
        facts = _resolve(report, exec_section.get(key, []))
        if not facts:
            continue
        add(f"### {title}")
        add("")
        for fact in facts:
            add(_fact_line(fact))
        add("")

    # 3. SEO opportunities
    seo = report.sections.get("seo_opportunities", {})
    add("## SEO opportunities")
    add("")
    _render_group(report, add, seo, [
        ("Gaining visibility", "gaining_visibility"),
        ("Losing clicks", "losing_clicks"),
        ("High impressions, weak CTR", "high_impressions_weak_ctr"),
    ])
    _render_inference_group(report, add, seo, [
        ("Ranking-threshold opportunities", "ranking_threshold_opportunities"),
        ("Content optimization / expansion", "content_opportunities"),
    ])

    # 4. Landing-page / CRO findings
    pages = report.sections.get("landing_pages", {})
    add("## Landing-page and CRO findings")
    add("")
    _render_group(report, add, pages, [
        ("Top entrances", "top_entrances"),
        ("Traffic with weak engagement", "traffic_weak_engagement"),
        ("Conversion metrics", "conversion_opportunities"),
    ])
    _render_inference_group(report, add, pages, [
        ("Strong engagement, weak search visibility", "strong_engagement_weak_visibility"),
    ])

    # 5. UX / Clarity findings
    ux = report.sections.get("clarity_ux", {})
    add("## UX and Clarity findings")
    add("")
    _render_group(report, add, ux, [("Behavioural metrics", "ux_metrics")])
    _render_inference_group(report, add, ux, [("Friction findings", "friction_findings")])
    review = ux.get("pages_for_recording_review", [])
    if review:
        add("### Pages worth a manual recording review")
        add("")
        for entity in review:
            add(f"- {entity}")
        add("")

    # 6. Cross-source conclusions
    add("## Cross-source conclusions")
    add("")
    add("*Interpretations. Each references the facts it rests on, and lists what "
        "else could produce the same pattern. These are correlations, not causes.*")
    add("")
    if not report.inferences:
        add("No cross-source signal fired this period.")
        add("")
    for inference in report.inferences:
        add(f"### {inference.signal.replace('_', ' ')} — {inference.entity_id}")
        add("")
        add(f"{inference.statement}")
        add("")
        add(f"- Confidence: {inference.confidence}")
        add(f"- Based on facts: {', '.join(f'`{f}`' for f in inference.based_on)}")
        add("- Could also be explained by:")
        for alternative in inference.alternative_explanations:
            add(f"  - {alternative}")
        add("")

    # 7. Prioritized actions
    add("## Prioritized actions")
    add("")
    if not report.recommendations:
        add("No recommendations this period.")
        add("")
    else:
        inferences = _inference_lookup(report)
        for priority in (PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_MONITOR):
            group = [r for r in report.recommendations if r.priority == priority]
            if not group:
                continue
            add(f"### {priority}")
            add("")
            for rec in group:
                add(f"**{rec.action}**")
                add("")
                add(f"- Area: {rec.area}")
                add(f"- Rationale: {rec.rationale}")
                add(f"- Supporting facts: {', '.join(f'`{f}`' for f in rec.supporting_facts)}")
                if rec.supporting_inferences:
                    signals = ", ".join(
                        inferences[i].signal for i in rec.supporting_inferences
                        if i in inferences
                    )
                    add(f"- From signal(s): {signals}")
                plan = rec.measurement_plan
                add(f"- Measurement plan: track `{plan.metric}` for `{plan.entity_id}` "
                    f"to {plan.direction} over {plan.min_observation_days} days "
                    f"(minimum sample {plan.min_sample:.0f})")
                add(f"- Confidence: {rec.confidence} · Readiness: {rec.readiness}")
                add("")

    # 8. Data quality and readiness
    add("## Data quality and readiness")
    add("")
    add(f"- Readiness: **{report.readiness}** — {report.readiness_note}")
    coverage = report.data_coverage.get("clarity_ledger", {})
    add(f"- Clarity ledger: {report.data_coverage.get('clarity_note', 'unknown')}")
    if coverage:
        add(f"  - days stored: {coverage.get('days_available', 0)}; "
            f"period covered: {coverage.get('supports_period', False)}; "
            f"comparison available: {coverage.get('supports_comparison', False)}")
    quality = report.data_quality
    conversions = quality.get("conversions") or {}
    if conversions:
        state = conversions.get("state")
        marker = "**Conversions unavailable**" if state != "ok" else "Conversions"
        add(f"- {marker}: {conversions.get('message', '')}")
    hydration = quality.get("hydration") or {}
    if hydration.get("used"):
        add(f"- Google data hydrated on demand for {len(hydration.get('windows', []))} "
            f"window(s) in {hydration.get('api_calls_made', 0)} read-only API call(s); "
            "not persisted. Clarity read from the durable ledger.")
        for error in hydration.get("errors", []):
            add(f"  - hydration issue: {error}")
    excluded = quality.get("excluded_non_production_records", 0)
    if excluded:
        hosts = ", ".join(h for h in quality.get("excluded_hosts", []) if h)
        add(f"- Excluded {excluded} non-production record(s) from: {hosts}. "
            "Deliberate, not data loss.")
    else:
        add("- No non-production records needed excluding this period.")
    instrumentation = [a for a in report.anomalies if a.is_instrumentation]
    if instrumentation:
        add(f"- **{len(instrumentation)} instrumentation anomaly(ies)** — "
            "recommendations for the affected entities are suppressed:")
        for anomaly in instrumentation:
            add(f"  - {anomaly.description}")
    else:
        add("- No instrumentation anomalies detected.")
    performance = [a for a in report.anomalies if not a.is_instrumentation]
    if performance:
        add(f"- {len(performance)} performance anomaly(ies):")
        for anomaly in performance:
            add(f"  - {anomaly.description}")
    add("")
    add("---")
    add("")
    add("*Read-only analysis. No change has been made to the site, GA4, Search "
        "Console, Clarity, or WordPress.*")

    return "\n".join(out)


def _render_group(report, add, section, entries):
    for title, key in entries:
        facts = _resolve(report, section.get(key, []))
        if not facts:
            continue
        add(f"### {title}")
        add("")
        for fact in facts:
            scope = "" if fact.entity_id == "site" else f" — `{fact.entity_id}`"
            eligibility = "" if fact.meets_minimum else " *(below minimum sample)*"
            add(f"- **{label(fact.metric)}**{scope}: "
                f"{format_value(fact.metric, fact.period_value)} "
                f"({format_change(fact)}){eligibility} `{fact.id}`")
        add("")


def _render_inference_group(report, add, section, entries):
    lookup = _inference_lookup(report)
    for title, key in entries:
        items = [lookup[i] for i in section.get(key, []) if i in lookup]
        if not items:
            continue
        add(f"### {title}")
        add("")
        for inference in items:
            add(f"- {inference.statement} ({inference.confidence} confidence) "
                f"`{inference.id}`")
        add("")


def _priority_counts(report):
    counts = {PRIORITY_HIGH: 0, PRIORITY_MEDIUM: 0, PRIORITY_MONITOR: 0}
    for rec in report.recommendations:
        counts[rec.priority] = counts.get(rec.priority, 0) + 1
    return counts
