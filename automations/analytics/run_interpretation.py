#!/usr/bin/env python3
"""
Run the interpretation graph over one stored weekly report.

This is the only entry point that spends money, and it is the last thing the
weekly workflow does. Everything it reads is already durable before it starts:
the report has been generated, persisted to GCS, uploaded as an artifact, and
rendered to the dashboard. Nothing here can reach back and affect any of that.

    python3 run_interpretation.py --report-date 2026-08-13 --persist

Exit codes:
    0  produced (and persisted, if asked)
    1  could not run — no key, no report, storage failure
    2  produced but could not persist
    3  already published for this week; nothing was overwritten
    4  disabled by INTERPRETATION_ENABLED

The workflow treats every one of these as non-fatal. They are distinguished so
a log reader can tell "we chose not to run" from "we tried and could not",
which is exactly the distinction that gets lost when a step is simply allowed
to fail.
"""

import argparse
import datetime as dt
import json
import os
import sys

import intelligence_store as istore
import interpretation_graph as ig
import marketing_intelligence as mi
import report_store as rs
from interpretation_caller import AnthropicCaller, CallerError
from storage import LocalFileStore, StorageError

ENABLED_ENV = "INTERPRETATION_ENABLED"


def enabled(env=None):
    env = os.environ if env is None else env
    return (env.get(ENABLED_ENV) or "true").strip().lower() not in ("false", "0", "no")


def build_store(args):
    bucket = args.gcs_bucket or os.environ.get("ANALYTICS_BUCKET", "").strip()
    if bucket:
        from storage_gcs import GCSStore

        return GCSStore(bucket, prefix=args.gcs_prefix)
    return LocalFileStore(args.store_root)


def resolve_report_date(store, explicit=None):
    """The date to interpret: the one given, else whatever `latest` points at."""
    if explicit:
        return explicit
    pointer = json.loads(store.get_text(rs.LATEST_KEY))
    date = pointer.get("report_date")
    if not date:
        raise StorageError(f"{rs.LATEST_KEY} carries no report_date")
    return date


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=("Interpret one stored weekly report and write the "
                     "Analytics -> Marketing Strategy handoff."))
    parser.add_argument("--report-date", default=None,
                        help="YYYY-MM-DD (default: whatever latest.json points at)")
    parser.add_argument("--out", default=None,
                        help="Also write the document to this local path")
    parser.add_argument("--persist", action="store_true",
                        help="Store it beside the report it was derived from")
    parser.add_argument("--gcs-bucket", default=None)
    parser.add_argument("--gcs-prefix", default="")
    parser.add_argument("--store-root", default="analytics-data")
    parser.add_argument("--dry-run", action="store_true",
                        help="Resolve inputs and print the plan; make no model call")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if not enabled():
        print(f"{ENABLED_ENV} is off; the interpretation graph did not run.")
        return 4

    try:
        store = build_store(args)
        report_date = resolve_report_date(store, args.report_date)
        document, report_key = istore.load_report(store, report_date)
    except StorageError as exc:
        print(f"FAIL could not read the stored report: {exc}", file=sys.stderr)
        return 1

    target = istore.key_for(report_date)
    print(f"Report:       {report_key}")
    print(f"Report date:  {report_date}")
    print(f"Readiness:    {document.get('readiness')}")
    print(f"Facts:        {len(document.get('facts', []))}")
    print(f"Destination:  {target}")

    if args.persist and store.exists(target):
        print("\nAn interpretation for this week is already published; it was "
              "left untouched.", file=sys.stderr)
        return 3

    caller = AnthropicCaller()
    print(f"Models:       " + ", ".join(
        f"{role}={cfg['model']}/{cfg['effort']}/{cfg['max_tokens']}t"
        for role, cfg in caller.config.items()))

    if args.dry_run:
        print("\nDry run — no model call was made and nothing was written.")
        return 0

    now = dt.datetime.now(dt.timezone.utc)
    try:
        result = ig.run_graph(document, caller, now=now)
    except (CallerError, ig.BudgetExceeded) as exc:
        print(f"FAIL the graph could not complete: {exc}", file=sys.stderr)
        return 1

    # Measured spend, recorded next to the caps it was bounded by.
    result["manifest"]["usage"] = caller.usage_summary()
    intelligence = mi.build(document, result, now=now)

    problems = mi.validate(intelligence)
    if problems:
        print("FAIL the handoff document failed its own validator:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    manifest = result["manifest"]
    usage = manifest["usage"]
    print(f"\nRun status:   {manifest['status']}")
    print(f"Specialists:  ran={manifest['specialists']['ran']} "
          f"skipped={manifest['specialists']['skipped_missing_input']} "
          f"failed={manifest['specialists']['failed']}")
    print(f"Findings:     {len(intelligence['verified_findings'])} verified, "
          f"{len(intelligence['excluded_findings'])} excluded")
    print(f"Calls:        {manifest['budget']['calls_made']} "
          f"retries={manifest['budget']['retries']}")
    print(f"Tokens:       in={usage['input_tokens']:,} "
          f"out={usage['output_tokens']:,} over {usage['attempts']} attempts")
    if usage["truncated_calls"]:
        print(f"::warning::truncated at the token ceiling: "
              f"{usage['truncated_calls']}")

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(intelligence, handle, indent=2, ensure_ascii=False)
        print(f"Wrote {args.out}")

    if args.persist:
        try:
            key = istore.publish(store, intelligence, report_date)
        except istore.AlreadyPublished as exc:
            print(f"\n{exc}", file=sys.stderr)
            return 3
        except StorageError as exc:
            print(f"\nProduced, but could not persist: {exc}", file=sys.stderr)
            return 2
        print(f"Persisted {key}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
