#!/usr/bin/env python3
"""
Run the Marketing Analysis Agent over stored history.

Read-only in every direction: it reads the durable store Phase 1 writes and
calls no external API. Clarity comes from the ledger, never from fresh
overlapping API windows, so running this costs nothing against Clarity's daily
budget.

It writes nothing to the site, GA4, Search Console, Clarity or WordPress, and
applies no recommendation anywhere. Output is a JSON analysis object and a
Markdown report; delivering either to anyone is a separate, later decision.

There is no schedule. This is a manual entry point.

Usage:
    # against the durable store
    export ANALYTICS_BUCKET=molosoc-analytics-history
    export ANALYTICS_STORAGE_SA_JSON='...'
    python3 automations/analytics/analyze_cli.py --format markdown

    # against a local store
    python3 automations/analytics/analyze_cli.py --store-root ./analytics-data

    # against deterministic fixtures, no storage or credentials at all
    python3 automations/analytics/analyze_cli.py --fixture healthy
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
import tracking as tr
from analysis_model import INSUFFICIENT_DATA
from storage import LocalFileStore

FIXTURES = {
    "low_volume": fx.low_volume_records,
    "healthy": fx.healthy_records,
    "broken": fx.broken_instrumentation_records,
}


def build_store(args):
    bucket = args.gcs_bucket or os.environ.get("ANALYTICS_BUCKET", "").strip()
    if bucket:
        from storage_gcs import GCSStore

        return GCSStore(bucket, prefix=args.gcs_prefix)
    return LocalFileStore(args.store_root)


def run_fixture(name, today, now):
    windows = pr.build_windows(today=today)
    period, prior = FIXTURES[name]()
    coverage = pr.ledger_coverage(
        windows[pr.PERIOD].dates() + windows[pr.PRIOR].dates(), windows
    )
    return analysis.analyse(period, prior, fx.baseline_records(), windows,
                            clarity_coverage=coverage, now=now)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=("Run the Molosoc Marketing Analysis Agent over stored history. "
                     "Read-only: makes no API call and changes nothing.")
    )
    parser.add_argument("--fixture", choices=sorted(FIXTURES),
                        help="Analyse a deterministic fixture instead of stored "
                             "history. Needs no storage or credentials.")
    parser.add_argument("--gcs-bucket", default=None,
                        help="Cloud Storage bucket (default: ANALYTICS_BUCKET)")
    parser.add_argument("--gcs-prefix", default="")
    parser.add_argument("--store-root", default="analytics-data",
                        help="Local store directory when no bucket is configured")
    parser.add_argument("--today", default=None,
                        help="Override today's date (YYYY-MM-DD) for a past analysis")
    parser.add_argument("--format", choices=("markdown", "json", "both"),
                        default="markdown")
    parser.add_argument("--out", default=None,
                        help="Write the output to this path instead of stdout")
    parser.add_argument("--update-ledger", action="store_true",
                        help="Merge this run's recommendations into the tracking "
                             "ledger. Off by default — analysing is read-only.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    now = dt.datetime.now(dt.timezone.utc)

    if args.fixture:
        report = run_fixture(args.fixture, args.today or "2026-08-17", now)
        store = None
    else:
        store = build_store(args)
        report = analysis.analyse_from_store(store, today=args.today, now=now)

    if args.update_ledger:
        if store is None:
            sys.exit("--update-ledger needs a real store, not a fixture run.")
        ledger = tr.merge_into_ledger(tr.load_ledger(store), report.recommendations, now=now)
        tr.save_ledger(store, ledger)

    if args.format == "json":
        output = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
    elif args.format == "markdown":
        output = render.render_markdown(report)
    else:
        output = (render.render_markdown(report) + "\n\n---\n\n```json\n"
                  + json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n```")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(output + "\n")
        print(f"Wrote {args.out}")
    else:
        print(output)

    # A low-volume report is a successful run, not a failure — the agent
    # correctly declining to advise is the designed behaviour.
    if report.readiness == INSUFFICIENT_DATA:
        print("\n(Analysis complete. Readiness: insufficient data for recommendation.)",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
