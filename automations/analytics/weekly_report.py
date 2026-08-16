#!/usr/bin/env python3
"""
Generate one weekly Molosoc marketing analysis report as Markdown.

Wraps the Phase 2 analysis engine with the weekly run's specific contract:

  * The latest complete 7-day period against the one before it. Search
    Console's 3-day finalisation lag sets the anchor, so a Wednesday run
    analyses the previous Monday-to-Sunday week against the week before.
  * GA4 and Search Console are hydrated read-only for exactly those two
    windows — four API calls, cached so a window is never fetched twice.
  * Clarity is read only from the durable ledger. **Zero fresh Clarity API
    calls.** Its API cannot return history anyway, and the daily collector
    owns the 10-calls-per-day budget; a report that spent from it could
    starve the collector and lose a day of history permanently.

Read-only in every direction. Nothing is written to the site, GA4, Search
Console, Clarity, WordPress, or the analytics history. The report is written to
a local file for the workflow to upload as an artifact, and is never committed.

No delivery of any kind: no email, no Slack, no dashboard.

Usage:
    export ANALYTICS_BUCKET=molosoc-analytics-history
    export ANALYTICS_STORAGE_SA_JSON='...'
    export GOOGLE_SERVICE_ACCOUNT_JSON='...'
    python3 automations/analytics/weekly_report.py --out-dir reports

    # deterministic fixture run, no credentials or storage at all
    python3 automations/analytics/weekly_report.py --fixture low_volume --out-dir /tmp
"""

import argparse
import datetime as dt
import json
import os
import sys

import analysis
import fixtures as fx
import periods as pr
import render
from analysis_model import INSUFFICIENT_DATA, PRIORITY_HIGH, PRIORITY_MEDIUM
from records import CLARITY
from storage import InMemoryStore, LocalFileStore

REPORT_PREFIX = "molosoc-marketing-analysis"

FIXTURES = {
    "low_volume": fx.low_volume_records,
    "healthy": fx.healthy_records,
    "broken": fx.broken_instrumentation_records,
}


def report_filename(report, extension="md"):
    """Dated, sortable, and stable for a given analysis period."""
    return f"{REPORT_PREFIX}-{report.as_of_date}.{extension}"


def build_store(args):
    bucket = args.gcs_bucket or os.environ.get("ANALYTICS_BUCKET", "").strip()
    if bucket:
        from storage_gcs import GCSStore

        return GCSStore(bucket, prefix=args.gcs_prefix)
    return LocalFileStore(args.store_root)


def build_hydrator():
    """The live read-only GA4 + Search Console hydrator."""
    import google_hydrate as gh

    return gh.live_hydrator()


def generate(store, hydrator, today=None, now=None, ecommerce_tracking_start=None):
    """Run the analysis for the weekly windows and render it.

    Returns (report, markdown). Clarity is read from `store` only — this
    function never constructs a Clarity API client.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    report = analysis.analyse_from_store(
        store, today=today, period_days=pr.DEFAULT_PERIOD_DAYS, now=now,
        hydrator=hydrator, ecommerce_tracking_start=ecommerce_tracking_start,
    )
    return report, render.render_markdown(report)


def generate_from_fixture(name, today="2026-08-17", now=None):
    """Deterministic run for tests and for previewing the output format."""
    now = now or dt.datetime(2026, 8, 17, 6, 0, tzinfo=dt.timezone.utc)
    store = InMemoryStore()
    period, prior = FIXTURES[name]()
    fx.store_with(store, [r for r in period + prior if r.source == CLARITY]
                  + fx.baseline_records())

    import google_hydrate as gh

    hydrator = gh.GoogleHydrator(
        ga4_fetcher=fx.fixture_ga4_fetcher(name),
        gsc_fetcher=fx.fixture_gsc_fetcher(name),
        collected_at=now.replace(microsecond=0).isoformat(),
    )
    return generate(store, hydrator, today=today, now=now)


def summarise_run(report):
    """One-line run summary for the workflow log — no credentials, no payloads."""
    counts = {p: 0 for p in (PRIORITY_HIGH, PRIORITY_MEDIUM, "Monitor")}
    for rec in report.recommendations:
        counts[rec.priority] = counts.get(rec.priority, 0) + 1
    hydration = report.data_quality.get("hydration", {})
    coverage = report.data_quality.get("tracking_coverage", {})
    return {
        "period": f"{report.period['start']}..{report.period['end']}",
        "comparison": (f"{report.comparison_periods[0]['start']}.."
                       f"{report.comparison_periods[0]['end']}"),
        "readiness": report.readiness,
        "facts": len(report.facts),
        "inferences": len(report.inferences),
        "recommendations": counts,
        "google_api_calls": hydration.get("api_calls_made", 0),
        "clarity_api_calls": 0,  # by construction: ledger only
        "clarity_ledger_days": report.data_coverage.get(
            "clarity_ledger", {}).get("days_available", 0),
        "conversions": report.data_quality.get("conversions", {}).get("state"),
        "tracking_coverage": coverage.get("state"),
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=("Generate the weekly Molosoc marketing analysis report. "
                     "Read-only; makes zero Clarity API calls.")
    )
    parser.add_argument("--out-dir", default="reports",
                        help="Directory to write the report into (default: reports)")
    parser.add_argument("--fixture", choices=sorted(FIXTURES),
                        help="Use deterministic fixture data instead of live sources")
    parser.add_argument("--today", default=None,
                        help="Override today's date (YYYY-MM-DD)")
    parser.add_argument("--gcs-bucket", default=None)
    parser.add_argument("--gcs-prefix", default="")
    parser.add_argument("--store-root", default="analytics-data")
    parser.add_argument("--also-json", action="store_true",
                        help="Also write the machine-readable analysis object")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    now = dt.datetime.now(dt.timezone.utc)

    if args.fixture:
        report, markdown = generate_from_fixture(args.fixture, args.today or "2026-08-17")
    else:
        store = build_store(args)
        report, markdown = generate(store, build_hydrator(), today=args.today, now=now)

    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, report_filename(report))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(markdown + "\n")
    print(f"Wrote {path}")

    if args.also_json:
        json_path = os.path.join(args.out_dir, report_filename(report, "json"))
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(report.to_dict(), handle, indent=2, ensure_ascii=False)
        print(f"Wrote {json_path}")

    summary = summarise_run(report)
    print("\nRun summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # A low-volume report is a successful run. The agent declining to advise is
    # the designed behaviour, not a failure to alert on.
    if report.readiness == INSUFFICIENT_DATA:
        print("\nReadiness: insufficient data for recommendation — facts reported, "
              "actions withheld.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
