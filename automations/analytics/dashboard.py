#!/usr/bin/env python3
"""
Render the weekly analysis as a single self-contained HTML page.

The JSON report is the contract; this is a second view of it, exactly as
render.py is the Markdown view. **Nothing is computed here.** Every number,
every delta, every readiness decision already exists in the report, so the page
and the Markdown cannot disagree and neither can drift from the analysis.

That rule has one consequence worth stating: the dashboard cannot promote a
recommendation the engine withheld. It renders `report["recommendations"]` and
nothing else, so the readiness gate holds here for free rather than by being
re-implemented and kept in sync.

The Email Marketing card is the one section fed by a second producer. It reads
the normalized email evidence document — the same artifact the dedicated email
report and the Growth Engine read — and never the rendered email page. Its
absence costs the card and nothing else.

Self-contained by design — brand tokens, layout and charts are inlined, so the
file opens with no network, no CDN, no build step and no JS framework. It is
one artefact you can upload, email or archive.

Visual language is the real Molosoc design system, lifted from
site/theme/assets/css/tokens.css rather than invented: ink #0c1115 on cream
#f8f7f4, peach accent, DM Serif Display over Mulish, generous whitespace.
Fonts fall back to system serif/sans when offline.

Usage:
    # from a stored report document
    python3 automations/analytics/dashboard.py --report report.json --out index.html

    # deterministic fixture, no credentials
    python3 automations/analytics/dashboard.py --fixture low_volume --out index.html
"""

import argparse
import datetime as dt
import html
import json
import sys

import email_summary
import render
import trafficdom_design as td
from analysis_model import (
    INSUFFICIENT_DATA, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_MONITOR,
)

SITE_ENTITY = "site"

# Site-level metrics per section, in reading order. Keeping the order here
# rather than deriving it from the report means a new metric appears in a
# deliberate place instead of wherever the analysis happened to emit it.
GA4_METRICS = ("ga4_sessions", "ga4_users", "ga4_views", "ga4_engagement_rate")
GSC_METRICS = ("gsc_clicks", "gsc_impressions", "gsc_ctr", "gsc_position")
CLARITY_METRICS = ("clarity_human_sessions", "clarity_sessions", "clarity_bot_share",
                   "clarity_scroll_depth", "clarity_rage_click_rate",
                   "clarity_dead_click_rate", "clarity_quickback_rate",
                   "clarity_script_error_rate")
ECOMMERCE_METRICS = ("ga4_key_event_purchase", "ga4_key_event_begin_checkout",
                     "ga4_key_event_add_to_cart")

TREND_METRICS = (
    ("ga4_sessions", "Sessions"),
    ("gsc_clicks", "Search clicks"),
    ("gsc_impressions", "Impressions"),
    ("clarity_human_sessions", "Clarity sessions"),
)

# Metrics where a lower number is the better outcome, so the colour of a
# change cannot be read off its sign alone.
LOWER_IS_BETTER = ("gsc_position", "clarity_bot_share", "clarity_rage_click_rate",
                   "clarity_dead_click_rate", "clarity_quickback_rate",
                   "clarity_script_error_rate")


def esc(value):
    return html.escape(str(value), quote=True)


# --------------------------------------------------------------------------
# Reading the report — dict access only, so this works on a stored document
# --------------------------------------------------------------------------

def facts_by_id(document):
    return {f["id"]: f for f in document.get("facts", [])}


def site_facts(document, metrics):
    """Site-level facts for the named metrics, in the order given."""
    found = {}
    for fact in document.get("facts", []):
        if fact.get("entity_type") == SITE_ENTITY and fact.get("metric") in metrics:
            found[fact["metric"]] = fact
    return [found[m] for m in metrics if m in found]


def page_facts(document, metric, limit=6):
    rows = [f for f in document.get("facts", [])
            if f.get("entity_type") == "page" and f.get("metric") == metric]
    return sorted(rows, key=lambda f: -(f.get("period_value") or 0))[:limit]


def query_facts(document, metric, limit=6):
    rows = [f for f in document.get("facts", [])
            if f.get("entity_type") == "query" and f.get("metric") == metric]
    return sorted(rows, key=lambda f: -(f.get("period_value") or 0))[:limit]


def fmt(metric, value):
    return render.format_value(metric, value)


def change_text(fact):
    """Delta as prose. Mirrors render.format_change, from dict rather than Fact."""
    if fact.get("comparison_value") is None:
        return "no comparison"
    delta = fact.get("delta_abs")
    if delta == 0:
        return "unchanged"
    sign = "+" if (delta or 0) > 0 else "−"
    pct = fact.get("delta_pct")
    if pct is None:
        return f"{sign}{fmt(fact['metric'], abs(delta))}"
    suffix = "" if fact.get("significant") else " · not significant"
    return f"{sign}{abs(pct):.0%}{suffix}"


def change_direction(fact):
    """'up' | 'down' | 'flat', by outcome rather than by sign.

    A rising average position is a worse result, and colouring it green
    because the number went up would be actively misleading.
    """
    delta = fact.get("delta_abs")
    if fact.get("comparison_value") is None or not delta:
        return "flat"
    improved = delta < 0 if fact["metric"] in LOWER_IS_BETTER else delta > 0
    return "up" if improved else "down"


# --------------------------------------------------------------------------
# Presentation — composed from the shared TrafficDom design system
# --------------------------------------------------------------------------
#
# Every component below comes from `trafficdom_design`, which is the Growth
# Engine's design system vendored into this repository (see that file's header).
# Nothing here writes markup or CSS: this module decides WHAT the Analytics
# report shows and in what order, and the design system decides how it looks.
#
# That split is the whole point. The Growth report is the same components in a
# different order, so the two pages are recognisably one suite without either
# repository importing the other.
#
# What each report emphasises stays different, because they answer different
# questions:
#
#   Analytics — what happened, what changed, how much of it we can trust
#   Growth    — what it means, what to focus on, what is not ready yet
#
# NOTHING IS COMPUTED HERE, exactly as before. Every number, delta and readiness
# decision already exists in the report document; this is a second view of it,
# so the page and the Markdown cannot disagree.


def metric_of(fact, trend=None):
    """One site metric as a shared metric card: value, movement, comparison."""
    metric = fact["metric"]
    notes = fact.get("notes") or {}

    # A missing comparison must never read as a zero. When the analysis recorded
    # WHY it is missing — most often that ecommerce tracking was not yet live —
    # say that instead of printing a bare dash and letting the reader assume.
    reason = notes.get("comparison_unavailable_reason")
    if fact.get("comparison_value") is None and reason:
        note = f"Previous period unmeasured — {reason}"
    else:
        note = f"Previous {fmt(metric, fact.get('comparison_value'))}"
    if not fact.get("meets_minimum", True):
        note += " · below minimum sample"

    return td.metric(
        value=fmt(metric, fact.get("period_value")),
        label=render.label(metric),
        note=note,
        change=change_text(fact),
        direction=change_direction(fact),
    )


def metric_grid(facts, empty_message):
    if not facts:
        return td.empty_state(empty_message)
    return td.metric_band([metric_of(fact) for fact in facts])


def entity_table(facts, heading, empty_message):
    """Top pages, top queries — the shared table, with the shared numerals."""
    if not facts:
        return td.empty_state(empty_message)
    rows = []
    for fact in facts:
        metric = fact["metric"]
        label = fact.get("entity_id") or "—"
        if not fact.get("meets_minimum", True):
            label += "  (low sample)"
        rows.append([label,
                     fmt(metric, fact.get("period_value")),
                     change_text(fact)])
    return td.data_table(
        ((heading, False), ("Period", True), ("Change", True)), rows)


def summary_section(document, headline, counts_text):
    """What happened this week, in one card — the Growth report's own opening.

    Same component, different question. Growth concludes ("what should we do");
    Analytics reports ("what happened, and can we trust it").
    """
    readiness = document.get("readiness", "")
    tone = "waiting" if readiness == INSUFFICIENT_DATA else "ready"
    label = ("More data needed" if readiness == INSUFFICIENT_DATA
             else "Measurement healthy")
    period = document.get("period") or {}
    comparison = document.get("comparison_period") or {}

    directives = [
        ("Period", f"{period.get('start', '')} to {period.get('end', '')}", False),
        ("Compared with",
         f"{comparison.get('start', '')} to {comparison.get('end', '')}"
         if comparison.get("start") else "No comparable previous period", False),
        ("Recommendations", counts_text, True),
    ]
    card = td.conclusion_card(
        status_label=label, tone=tone,
        period=f"Week to {document.get('report_date', '')}",
        statement=document.get("readiness_note", ""),
        directives=directives,
    )
    return card + metric_grid(headline, "No site-level metrics in this period.")


def trends_section(index):
    """Only rendered once there is a shape to see.

    History accumulates one week at a time from the first persisted report, so
    for the first weeks this section is honestly absent rather than a flat line
    pretending to be a trend.
    """
    entries = list(reversed((index or {}).get("entries", [])))
    if len(entries) < 3:
        return ""

    cards = []
    for metric, title in TREND_METRICS:
        points = [(e.get("report_date"), (e.get("headline_metrics") or {}).get(metric))
                  for e in entries]
        values = [value for _, value in points if value is not None]
        if len(values) < 2:
            continue
        latest = next((v for _, v in reversed(points) if v is not None), None)
        cards.append(td.metric(
            value=fmt(metric, latest), label=title,
            trend=values, trend_label=f"{title} over {len(values)} weeks"))

    if not cards:
        return ""
    first, last = entries[0].get("report_date"), entries[-1].get("report_date")
    return td.section(
        "Trend", td.metric_band(cards), eyebrow="History", anchor="trends",
        lede=f"{len(entries)} weekly reports, {first} to {last}. Shape only — "
             "the figures above are the measured values.",
    )


def recommendations_section(document):
    """The engine's own recommendations, in the shared priority row.

    The dashboard cannot promote a recommendation the engine withheld: it
    renders `document["recommendations"]` and nothing else, so the readiness
    gate holds here for free rather than by being re-implemented.
    """
    recs = document.get("recommendations", [])
    readiness = document.get("readiness")

    if not recs:
        reason = ("The analysis withheld recommendations at this volume."
                  if readiness == INSUFFICIENT_DATA
                  else "No recommendation cleared the thresholds this period.")
        return td.section(
            "Recommendations",
            td.empty_state(f"{reason} Nothing has been applied to the site."),
            eyebrow="Proposals", anchor="recommendations")

    order = {PRIORITY_HIGH: 0, PRIORITY_MEDIUM: 1, PRIORITY_MONITOR: 2}
    tones = {PRIORITY_HIGH: "ready", PRIORITY_MEDIUM: "waiting",
             PRIORITY_MONITOR: "off"}
    rows = []
    for rank, rec in enumerate(sorted(recs, key=lambda r: order.get(r.get("priority"), 9)),
                               start=1):
        priority = rec.get("priority", PRIORITY_MONITOR)
        plan = rec.get("measurement_plan") or {}
        rows.append(td.priority_row(
            rank=rank,
            channel=rec.get("area", ""),
            title=rec.get("action", ""),
            why=rec.get("rationale", ""),
            state_label=f"{priority} priority",
            tone=tones.get(priority, "off"),
            recommended=priority == PRIORITY_HIGH,
            priority_label=(f"Measured by {render.label(plan.get('metric', ''))} "
                            f"over {plan.get('min_observation_days', 28)} days"),
        ))
    return td.section(
        "Recommendations", td.priority_list(rows), eyebrow="Proposals",
        anchor="recommendations",
        lede="Proposed for a human to decide on. Nothing here has been applied.")


def quality_drawer(document, generated):
    """Readiness, coverage and caveats — present, out of the reading path.

    The Growth report puts its internal states behind the same drawer. A reader
    who wants to audit either report opens the same thing in the same place.
    """
    quality = document.get("data_quality", {})
    coverage = document.get("source_coverage", {})
    conversions = document.get("conversions", {})
    boundary = document.get("ecommerce_tracking_boundary", {})
    tracking = document.get("tracking_coverage", {})
    ledger = coverage.get("clarity_ledger", {})
    hydration = quality.get("hydration", {})

    rows = []
    if conversions.get("message"):
        rows.append(("Conversions", conversions["message"]))
    if boundary.get("message"):
        rows.append(("Ecommerce tracking boundary", boundary["message"]))
    if tracking.get("headline"):
        rows.append(("Tracking coverage (GA4 vs Clarity)", tracking["headline"]))
    if ledger.get("message"):
        rows.append(("Clarity history", ledger["message"]))
    if hydration.get("note"):
        rows.append(("Google data", hydration["note"]))
    if quality.get("excluded_non_production_records"):
        hosts = ", ".join(quality.get("excluded_hosts", []) or [])
        rows.append(("Excluded", f"{quality['excluded_non_production_records']} "
                                 f"non-production record(s) from {hosts}. Deliberate."))
    rows.append(("Report", f"{document.get('report_id', '')}, schema "
                           f"{document.get('schema_version', '')}, generated "
                           f"{generated}"))

    return td.technical_drawer([
        td.technical_table("Readiness and data quality", rows),
        td.technical_list("Coverage caveats", tracking.get("caveats") or []),
    ], summary="Technical evidence")


# --------------------------------------------------------------------------
# The page
# --------------------------------------------------------------------------

#: Where the dedicated Email Marketing report is served from. Used only to link
#: to it. Committed rather than read from the email document, because a URL
#: that arrived inside an artifact would be untrusted input pointing wherever
#: it liked — and this page is what a client opens.
EMAIL_REPORT_URL = "https://trafficdom.com/reports/molosoc/email-marketing/"


def render_dashboard(document, index=None, generated_at=None, email=None):
    """Return the complete self-contained HTML page as a string.

    ``email`` is the normalized email evidence document, or ``None`` when none
    has been published. It is the ARTIFACT, never the rendered email report: a
    dashboard that scraped another page for numbers would empty itself the
    first time that page's layout changed.
    """
    generated = generated_at or document.get("generated_at", "")

    ga4 = site_facts(document, GA4_METRICS)
    gsc = site_facts(document, GSC_METRICS)
    clarity = site_facts(document, CLARITY_METRICS)
    ecommerce = site_facts(document, ECOMMERCE_METRICS)
    headline = ga4[:2] + gsc[:2]

    conversion_note = (document.get("conversions", {}) or {}).get("message", "")

    counts = {}
    for rec in document.get("recommendations", []):
        counts[rec.get("priority")] = counts.get(rec.get("priority"), 0) + 1
    counts_text = " · ".join(
        f"{counts.get(p, 0)} {p}" for p in (PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_MONITOR)
    )

    body = td.wrap([
        td.report_header(
            title="Molosoc — Weekly Analytics",
            eyebrow="What happened this week, and how much of it we can trust.",
            facts=[
                ("Report date", document.get("report_date", "")),
                ("Schema", document.get("schema_version", "")),
                ("Sources", "GA4, Search Console, Clarity"
                            + (", Email" if email else "")),
            ],
            wordmark="TrafficDom Analytics",
        ),
        summary_section(document, headline, counts_text),
        td.section("Traffic", metric_grid(ga4, "No GA4 metrics in this period.")
                   + entity_table(page_facts(document, "ga4_sessions"),
                                  "Top landing pages",
                                  "No page-level GA4 data in this period."),
                   eyebrow="GA4", anchor="ga4"),
        td.section("Search", metric_grid(gsc, "No Search Console metrics in this period.")
                   + entity_table(query_facts(document, "gsc_clicks"), "Top queries",
                                  "No query-level data in this period.")
                   + entity_table(page_facts(document, "gsc_clicks"),
                                  "Top pages in search",
                                  "No page-level search data in this period."),
                   eyebrow="Search Console", anchor="seo"),
        td.section("Behaviour",
                   metric_grid(clarity,
                               "No Clarity metrics in this period. Clarity history "
                               "accumulates forward from the daily collector and "
                               "cannot be backfilled."),
                   eyebrow="Clarity", anchor="clarity"),
        td.section("Ecommerce and conversions",
                   td.note_panel("", conversion_note)
                   + metric_grid(ecommerce,
                                 conversion_note
                                 or "No conversion metrics in this period."),
                   eyebrow="Conversions", anchor="ecommerce"),
        email_summary.email_section(email, EMAIL_REPORT_URL),
        trends_section(index),
        recommendations_section(document),
        quality_drawer(document, generated),
        td.footer(statement=(
            "Read-only analysis produced by TrafficDom. No change has been made "
            "to the site, GA4, Search Console, Clarity or WordPress. "
            "Recommendations are proposals for a human to decide on.")),
    ])

    title = (f"Molosoc — Weekly Marketing Analysis "
             f"{document.get('report_date', '')} | TrafficDom")
    return td.page(title, body)


def document_from_fixture(name, today="2026-08-17"):
    """Deterministic document for tests and offline previews."""
    import report_store as rs
    import weekly_report as wr

    report, _markdown = wr.generate_from_fixture(name, today=today)
    return rs.build_document(report)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Render the weekly analysis as a self-contained HTML page.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--report", help="Path to a stored report JSON document")
    source.add_argument("--fixture", choices=("low_volume", "healthy", "broken"),
                        help="Deterministic fixture instead of a real report")
    parser.add_argument("--index", help="Path to index.json, for the trend section")
    parser.add_argument("--email", default=None,
                        help="Path to the normalized email evidence document. "
                             "Its absence costs the Email card, not the page.")
    parser.add_argument("--out", default="index.html", help="Output path (default: index.html)")
    parser.add_argument("--today", default="2026-08-17", help="Fixture date override")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.fixture:
        document = document_from_fixture(args.fixture, args.today)
    else:
        with open(args.report, "r", encoding="utf-8") as handle:
            document = json.load(handle)

    index = None
    if args.index:
        try:
            with open(args.index, "r", encoding="utf-8") as handle:
                index = json.load(handle)
        except (OSError, ValueError):
            index = None  # a missing index costs the trend strip, not the page

    # A missing or unreadable email document costs the Email card and nothing
    # else. A weekly report that failed because a second channel was quiet
    # would be a worse report than one with a card that says so.
    email = email_summary.load(args.email)

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    page = render_dashboard(document, index=index, generated_at=now, email=email)
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write(page)

    print(f"Wrote {args.out} ({len(page):,} bytes)")
    print(f"  period: {document.get('period', {}).get('start')}.."
          f"{document.get('period', {}).get('end')}")
    print(f"  readiness: {document.get('readiness')}")
    print(f"  recommendations: {len(document.get('recommendations', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
