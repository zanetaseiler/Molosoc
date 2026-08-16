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

import render
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
# Fragments
# --------------------------------------------------------------------------

def metric_card(fact):
    metric = fact["metric"]
    direction = change_direction(fact)
    notes = fact.get("notes") or {}

    # A missing comparison must never read as a zero. When the analysis
    # recorded WHY it is missing — most often that ecommerce tracking was not
    # yet live — say that instead of printing a bare dash and leaving the
    # reader to assume the worst.
    reason = notes.get("comparison_unavailable_reason")
    if fact.get("comparison_value") is None and reason:
        previous = f'<p class="ms-metric__prev">Previous period unmeasured — {esc(reason)}</p>'
    else:
        previous = (f'<p class="ms-metric__prev">prev '
                    f'{esc(fmt(metric, fact.get("comparison_value")))}</p>')

    flag = ("" if fact.get("meets_minimum", True)
            else '<span class="ms-flag">below minimum sample</span>')
    return f"""
      <article class="ms-metric ms-metric--{direction}">
        <p class="ms-metric__label">{esc(render.label(metric))}</p>
        <p class="ms-metric__value">{esc(fmt(metric, fact.get('period_value')))}</p>
        <p class="ms-metric__delta">{esc(change_text(fact))}</p>
        {previous}
        {flag}
      </article>"""


def metric_grid(facts, empty_message):
    if not facts:
        return f'<p class="ms-empty">{esc(empty_message)}</p>'
    return '<div class="ms-metrics">' + "".join(metric_card(f) for f in facts) + "</div>"


def entity_table(facts, heading, empty_message):
    if not facts:
        return f'<p class="ms-empty">{esc(empty_message)}</p>'
    rows = []
    for fact in facts:
        metric = fact["metric"]
        flag = "" if fact.get("meets_minimum", True) else ' <span class="ms-flag">low sample</span>'
        rows.append(
            f"<tr><td class='ms-cell-entity'>{esc(fact.get('entity_id') or '—')}{flag}</td>"
            f"<td class='ms-num'>{esc(fmt(metric, fact.get('period_value')))}</td>"
            f"<td class='ms-num ms-delta ms-delta--{change_direction(fact)}'>"
            f"{esc(change_text(fact))}</td></tr>"
        )
    return f"""
      <table class="ms-table">
        <thead><tr><th>{esc(heading)}</th><th class="ms-num">Period</th>
        <th class="ms-num">Change</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table>"""


def sparkline(points, width=240, height=44):
    """Inline SVG trend. Deliberately unlabelled — the number beside it is the
    fact; this only shows shape, and axes would imply a precision that a
    handful of weekly points does not carry."""
    values = [v for _, v in points if v is not None]
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    span = (high - low) or 1
    step = width / max(len(values) - 1, 1)
    coords = " ".join(
        f"{i * step:.1f},{height - ((v - low) / span) * (height - 8) - 4:.1f}"
        for i, v in enumerate(values)
    )
    last_x = (len(values) - 1) * step
    last_y = height - ((values[-1] - low) / span) * (height - 8) - 4
    return f"""
      <svg class="ms-spark" viewBox="0 0 {width} {height}" role="img"
           aria-label="trend across {len(values)} weeks" preserveAspectRatio="none">
        <polyline points="{coords}" fill="none" stroke="currentColor"
                  stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
        <circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="3" fill="currentColor"/>
      </svg>"""


def trends_section(index):
    """Only rendered once there is a shape to see.

    History accumulates one week at a time from the first persisted report, so
    for the first weeks this section is honestly absent rather than a flat line
    pretending to be a trend.
    """
    entries = list(reversed((index or {}).get("entries", [])))
    if len(entries) < 3:
        return ""

    blocks = []
    for metric, title in TREND_METRICS:
        points = [(e.get("report_date"), (e.get("headline_metrics") or {}).get(metric))
                  for e in entries]
        chart = sparkline(points)
        if not chart:
            continue
        latest = next((v for _, v in reversed(points) if v is not None), None)
        blocks.append(f"""
          <article class="ms-trend">
            <p class="ms-metric__label">{esc(title)}</p>
            <p class="ms-trend__value">{esc(fmt(metric, latest))}</p>
            {chart}
          </article>""")

    if not blocks:
        return ""
    first, last = entries[0].get("report_date"), entries[-1].get("report_date")
    return f"""
    <section class="ms-section" id="trends">
      <h2>Trend</h2>
      <p class="ms-section__note">{len(entries)} weekly reports, {esc(first)} to {esc(last)}.
      Shape only — the figures above are the measured values.</p>
      <div class="ms-trends">{''.join(blocks)}</div>
    </section>"""


def recommendations_section(document):
    recs = document.get("recommendations", [])
    readiness = document.get("readiness")

    if not recs:
        reason = ("The analysis withheld recommendations at this volume."
                  if readiness == INSUFFICIENT_DATA
                  else "No recommendation cleared the thresholds this period.")
        return f"""
    <section class="ms-section" id="recommendations">
      <h2>Recommendations</h2>
      <p class="ms-empty">{esc(reason)} Nothing has been applied to the site.</p>
    </section>"""

    order = {PRIORITY_HIGH: 0, PRIORITY_MEDIUM: 1, PRIORITY_MONITOR: 2}
    cards = []
    for rec in sorted(recs, key=lambda r: order.get(r.get("priority"), 9)):
        priority = rec.get("priority", PRIORITY_MONITOR)
        plan = rec.get("measurement_plan") or {}
        cards.append(f"""
        <article class="ms-rec ms-rec--{esc(priority.lower())}">
          <p class="ms-rec__tag">{esc(priority)} · {esc(rec.get('area', ''))}</p>
          <h3>{esc(rec.get('action', ''))}</h3>
          <p class="ms-rec__why">{esc(rec.get('rationale', ''))}</p>
          <p class="ms-rec__plan">Measured by
            <strong>{esc(render.label(plan.get('metric', '')))}</strong>
            over {esc(plan.get('min_observation_days', 28))} days.</p>
        </article>""")

    return f"""
    <section class="ms-section" id="recommendations">
      <h2>Recommendations</h2>
      <p class="ms-section__note">Proposed for a human to decide on.
      Nothing here has been applied.</p>
      <div class="ms-recs">{''.join(cards)}</div>
    </section>"""


def quality_section(document):
    quality = document.get("data_quality", {})
    coverage = document.get("source_coverage", {})
    conversions = document.get("conversions", {})
    boundary = document.get("ecommerce_tracking_boundary", {})
    tracking = document.get("tracking_coverage", {})
    ledger = coverage.get("clarity_ledger", {})
    hydration = quality.get("hydration", {})

    items = []
    if conversions.get("message"):
        items.append(("Conversions", conversions["message"]))
    if boundary.get("message"):
        items.append(("Ecommerce tracking boundary", boundary["message"]))
    if tracking.get("headline"):
        items.append(("Tracking coverage (GA4 vs Clarity)", tracking["headline"]))
    if ledger.get("message"):
        items.append(("Clarity history", ledger["message"]))
    if hydration.get("note"):
        items.append(("Google data", hydration["note"]))
    if quality.get("excluded_non_production_records"):
        hosts = ", ".join(quality.get("excluded_hosts", []) or [])
        items.append(("Excluded", f"{quality['excluded_non_production_records']} "
                                  f"non-production record(s) from {hosts}. Deliberate."))

    caveats = "".join(f"<li>{esc(c)}</li>" for c in (tracking.get("caveats") or []))
    caveat_block = (f'<details class="ms-caveats"><summary>Coverage caveats</summary>'
                    f'<ul>{caveats}</ul></details>' if caveats else "")

    rows = "".join(
        f"<div class='ms-quality__row'><p class='ms-quality__key'>{esc(k)}</p>"
        f"<p class='ms-quality__val'>{esc(v)}</p></div>" for k, v in items
    )
    return f"""
    <section class="ms-section" id="quality">
      <h2>Readiness and data quality</h2>
      <div class="ms-quality">{rows}</div>
      {caveat_block}
    </section>"""


# --------------------------------------------------------------------------
# The page
# --------------------------------------------------------------------------

def render_dashboard(document, index=None, generated_at=None):
    """Return the complete self-contained HTML page as a string."""
    period = document.get("period") or {}
    comparison = document.get("comparison_period") or {}
    readiness = document.get("readiness", "")
    ready_class = "warn" if readiness == INSUFFICIENT_DATA else "ok"
    generated = generated_at or document.get("generated_at", "")

    ga4 = site_facts(document, GA4_METRICS)
    gsc = site_facts(document, GSC_METRICS)
    clarity = site_facts(document, CLARITY_METRICS)
    ecommerce = site_facts(document, ECOMMERCE_METRICS)
    headline = ga4[:2] + gsc[:2]

    conversions = document.get("conversions", {})
    conversion_note = conversions.get("message", "")

    counts = {}
    for rec in document.get("recommendations", []):
        counts[rec.get("priority")] = counts.get(rec.get("priority"), 0) + 1
    counts_text = " · ".join(
        f"{counts.get(p, 0)} {p}" for p in (PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_MONITOR)
    )

    ecommerce_block = metric_grid(
        ecommerce,
        conversion_note or "No conversion metrics in this period.")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>Molosoc marketing analysis — {esc(document.get('report_date', ''))}</title>
<!--
  Generated from the weekly analysis report, schema {esc(document.get('schema_version', ''))}.
  Every figure on this page exists in that JSON; nothing is recomputed here, so
  this view and the Markdown report cannot disagree. Read-only: no change has
  been made to the site, GA4, Search Console, Clarity or WordPress.
-->
<style>
:root {{
  --color-ink: #0c1115;
  --color-ink-muted: #6a6b6c;
  --color-white: #fff;
  --color-cream: #f8f7f4;
  --color-cream-deep: #efeee9;
  --color-accent-peach: #e3c4a8;
  --color-up: #2f6b4f;
  --color-down: #a1442f;
  --font-display: "DM Serif Display", Georgia, "Times New Roman", serif;
  --font-body: "Mulish", "Muli", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --radius-m: 10px;
  --shadow-soft: 0 12px 40px -16px rgba(12, 17, 21, .18);
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0; background: var(--color-cream); color: var(--color-ink);
  font-family: var(--font-body); font-size: 17px; line-height: 1.7;
  -webkit-font-smoothing: antialiased;
}}
.ms-wrap {{ max-width: 72rem; margin: 0 auto; padding: clamp(1.5rem, 5vw, 4.5rem) clamp(1.1rem, 4vw, 3rem); }}
h1, h2, h3 {{ font-family: var(--font-display); font-weight: 400; letter-spacing: -.01em; }}
h1 {{ font-size: clamp(2rem, 4vw + 1rem, 3.4rem); line-height: 1.1; margin: 0 0 .4rem; }}
h2 {{ font-size: clamp(1.4rem, 1.6vw + 1rem, 2rem); margin: 0 0 .35rem; }}
h3 {{ font-size: 1.15rem; margin: 0 0 .4rem; line-height: 1.3; }}
p {{ margin: 0 0 .5rem; }}

.ms-head {{ border-bottom: 1px solid rgba(12,17,21,.1); padding-bottom: 1.6rem; margin-bottom: 2.2rem; }}
.ms-eyebrow {{ font-size: .8125rem; letter-spacing: .14em; text-transform: uppercase;
  color: var(--color-ink-muted); margin: 0 0 .6rem; }}
.ms-period {{ font-size: 1.0625rem; color: var(--color-ink-muted); }}
.ms-period strong {{ color: var(--color-ink); font-weight: 600; }}

.ms-badge {{ display: inline-block; padding: .3rem .8rem; border-radius: 999px;
  font-size: .8125rem; letter-spacing: .04em; margin-top: .9rem; }}
.ms-badge--ok {{ background: rgba(47,107,79,.12); color: var(--color-up); }}
.ms-badge--warn {{ background: var(--color-accent-peach); color: #5c3a1e; }}

.ms-summary {{ background: var(--color-white); border-radius: var(--radius-m);
  padding: clamp(1.2rem, 3vw, 2rem); box-shadow: var(--shadow-soft); margin-bottom: 2.5rem; }}
.ms-summary__note {{ font-size: 1.0625rem; margin-bottom: 1.2rem; }}

.ms-section {{ margin: 0 0 2.8rem; }}
.ms-section__note {{ color: var(--color-ink-muted); font-size: .9375rem; margin-bottom: 1rem; }}

.ms-metrics {{ display: grid; gap: .9rem; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr)); }}
.ms-metric {{ background: var(--color-white); border-radius: var(--radius-m);
  padding: 1.1rem 1.2rem; border-top: 3px solid var(--color-cream-deep); }}
.ms-metric--up {{ border-top-color: var(--color-up); }}
.ms-metric--down {{ border-top-color: var(--color-down); }}
.ms-metric__label {{ font-size: .8125rem; letter-spacing: .06em; text-transform: uppercase;
  color: var(--color-ink-muted); margin-bottom: .3rem; }}
.ms-metric__value {{ font-family: var(--font-display); font-size: 2rem; line-height: 1.1; margin: 0 0 .25rem; }}
.ms-metric__delta {{ font-size: .9375rem; font-weight: 600; margin: 0; }}
.ms-metric--up .ms-metric__delta {{ color: var(--color-up); }}
.ms-metric--down .ms-metric__delta {{ color: var(--color-down); }}
.ms-metric__prev, .ms-flag {{ font-size: .8125rem; color: var(--color-ink-muted); margin: 0; }}
.ms-flag {{ display: inline-block; margin-top: .35rem; font-style: italic; }}

.ms-table {{ width: 100%; border-collapse: collapse; background: var(--color-white);
  border-radius: var(--radius-m); overflow: hidden; font-size: .9375rem; }}
.ms-table th {{ text-align: left; font-size: .75rem; letter-spacing: .08em; text-transform: uppercase;
  color: var(--color-ink-muted); font-weight: 600; padding: .8rem 1rem; background: var(--color-cream-deep); }}
.ms-table td {{ padding: .75rem 1rem; border-top: 1px solid rgba(12,17,21,.06); }}
.ms-num {{ text-align: right; white-space: nowrap; }}
.ms-cell-entity {{ word-break: break-all; }}
.ms-delta--up {{ color: var(--color-up); font-weight: 600; }}
.ms-delta--down {{ color: var(--color-down); font-weight: 600; }}
.ms-table + .ms-table {{ margin-top: 1rem; }}

.ms-trends {{ display: grid; gap: 1rem; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); }}
.ms-trend {{ background: var(--color-white); border-radius: var(--radius-m); padding: 1.1rem 1.2rem;
  color: var(--color-ink); }}
.ms-trend__value {{ font-family: var(--font-display); font-size: 1.6rem; margin: 0 0 .5rem; }}
.ms-spark {{ display: block; width: 100%; height: 44px; color: var(--color-accent-peach); }}

.ms-recs {{ display: grid; gap: 1rem; }}
.ms-rec {{ background: var(--color-white); border-radius: var(--radius-m); padding: 1.2rem 1.3rem;
  border-left: 4px solid var(--color-cream-deep); }}
.ms-rec--high {{ border-left-color: var(--color-down); }}
.ms-rec--medium {{ border-left-color: var(--color-accent-peach); }}
.ms-rec__tag {{ font-size: .75rem; letter-spacing: .1em; text-transform: uppercase;
  color: var(--color-ink-muted); margin-bottom: .4rem; }}
.ms-rec__why, .ms-rec__plan {{ font-size: .9375rem; color: var(--color-ink-muted); }}

.ms-quality {{ background: var(--color-white); border-radius: var(--radius-m); overflow: hidden; }}
.ms-quality__row {{ padding: .9rem 1.2rem; border-top: 1px solid rgba(12,17,21,.06); }}
.ms-quality__row:first-child {{ border-top: 0; }}
.ms-quality__key {{ font-size: .75rem; letter-spacing: .08em; text-transform: uppercase;
  color: var(--color-ink-muted); margin-bottom: .15rem; }}
.ms-quality__val {{ margin: 0; font-size: .9375rem; }}
.ms-caveats {{ margin-top: 1rem; font-size: .9375rem; color: var(--color-ink-muted); }}
.ms-caveats summary {{ cursor: pointer; }}
.ms-caveats ul {{ margin: .6rem 0 0; padding-left: 1.1rem; }}

.ms-empty {{ color: var(--color-ink-muted); font-style: italic; }}
.ms-foot {{ border-top: 1px solid rgba(12,17,21,.1); margin-top: 3rem; padding-top: 1.4rem;
  font-size: .875rem; color: var(--color-ink-muted); }}

@media (max-width: 40rem) {{
  body {{ font-size: 16px; }}
  .ms-metric__value {{ font-size: 1.7rem; }}
  .ms-table th, .ms-table td {{ padding: .6rem .7rem; }}
}}
@media print {{
  body {{ background: #fff; }}
  .ms-metric, .ms-summary, .ms-table, .ms-quality {{ box-shadow: none; border: 1px solid #ddd; }}
}}
</style>
</head>
<body>
<div class="ms-wrap">

  <header class="ms-head">
    <p class="ms-eyebrow">Molosoc · Weekly marketing analysis</p>
    <h1>{esc(document.get('report_date', ''))}</h1>
    <p class="ms-period">
      <strong>{esc(period.get('start', ''))} – {esc(period.get('end', ''))}</strong>
      compared with {esc(comparison.get('start', ''))} – {esc(comparison.get('end', ''))}
    </p>
    <span class="ms-badge ms-badge--{ready_class}">{esc(readiness.replace('_', ' '))}</span>
  </header>

  <section class="ms-summary" id="summary">
    <h2>Executive summary</h2>
    <p class="ms-summary__note">{esc(document.get('readiness_note', ''))}</p>
    {metric_grid(headline, "No site-level metrics in this period.")}
    <p class="ms-section__note" style="margin-top:1rem">Recommendations: {esc(counts_text)}</p>
  </section>

  <section class="ms-section" id="ga4">
    <h2>Traffic — GA4</h2>
    {metric_grid(ga4, "No GA4 metrics in this period.")}
    <div style="margin-top:1rem">
      {entity_table(page_facts(document, "ga4_sessions"), "Top landing pages",
                    "No page-level GA4 data in this period.")}
    </div>
  </section>

  <section class="ms-section" id="seo">
    <h2>Search Console — SEO</h2>
    {metric_grid(gsc, "No Search Console metrics in this period.")}
    <div style="margin-top:1rem">
      {entity_table(query_facts(document, "gsc_clicks"), "Top queries",
                    "No query-level data in this period.")}
      {entity_table(page_facts(document, "gsc_clicks"), "Top pages in search",
                    "No page-level search data in this period.")}
    </div>
  </section>

  <section class="ms-section" id="clarity">
    <h2>Behaviour — Clarity</h2>
    {metric_grid(clarity, "No Clarity metrics in this period. Clarity history "
                          "accumulates forward from the daily collector and cannot be backfilled.")}
  </section>

  <section class="ms-section" id="ecommerce">
    <h2>Ecommerce and conversions</h2>
    {f'<p class="ms-section__note">{esc(conversion_note)}</p>' if conversion_note else ''}
    {ecommerce_block}
  </section>

  {trends_section(index)}

  {recommendations_section(document)}

  {quality_section(document)}

  <footer class="ms-foot">
    <p>Generated {esc(generated)} from report {esc(document.get('report_id', ''))},
    schema {esc(document.get('schema_version', ''))}.</p>
    <p>Read-only analysis. No change has been made to the site, GA4, Search Console,
    Clarity or WordPress. Recommendations are proposals for a human to decide on.</p>
  </footer>

</div>
</body>
</html>
"""


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

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

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    page = render_dashboard(document, index=index, generated_at=now)
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
