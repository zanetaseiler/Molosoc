#!/usr/bin/env python3
"""
Collect one Clarity daily snapshot and store it durably.

Why this exists: Clarity's Live Insights endpoint returns at most three days.
GA4 and Search Console can reconstruct any past period on demand; Clarity
cannot. Its history therefore only exists if something records it day by day,
and no later work can backfill a day that was missed.

HOW DOUBLE-COUNTING IS PREVENTED — the important part.

`numOfDays=1` means "the trailing 24 hours from now", not "the calendar day".
Two consequences follow:

  * Snapshots are always taken with numOfDays=1, never 2 or 3. Consecutive
    multi-day windows overlap, so summing them double-counts.
  * At most one snapshot per UTC date becomes a daily bucket. A second run on
    the same date would cover an overlapping 24-hour window, so it is refused
    by default. --force stores it as an extra revision under the same date,
    marked superseding=False, and it never becomes a second daily bucket.

records.sum_metric() independently refuses to aggregate anything with
window_days > 1, so even a hand-written aggregation cannot double-count.

RATE LIMIT: one API call per run, reserved from the persisted daily budget
before the call is made. No retries.

READ-ONLY: the endpoint has no write operation; this issues a single GET.

The token is read from CLARITY_API_TOKEN only, registered with the redactor on
load, and sent solely in an Authorization header.

Usage:
    export CLARITY_API_TOKEN='...'
    python3 automations/analytics/clarity_daily_collect.py --store-root ./analytics-data
"""

import argparse
import datetime as dt
import sys

import requests

from analytics_common import describe_error
from call_budget import BudgetExhausted, ClarityCallBudget
from clarity_api import fetch_live_insights, load_api_token, validate_request
from normalize import clarity_records
from quality import assess_snapshot, worst_severity
from records import CLARITY, utc_now_iso
from storage import LocalFileStore, StorageError, facts_key, raw_key, raw_prefix

# Snapshots are always single-day. This is a constant, not an option: see the
# double-counting note above.
SNAPSHOT_NUM_DAYS = 1


class AlreadyCollected(RuntimeError):
    """A snapshot for this UTC date exists. Collecting again would overlap."""


def existing_snapshot_keys(store, date):
    return [k for k in store.list_keys(raw_prefix(CLARITY, date))]


def collect(store, token, session=None, date=None, budget=None, force=False,
            dimensions=(), now=None):
    """Fetch one snapshot, normalize it, assess quality, and store both layers.

    Returns a summary dict. Makes exactly one API call, and none at all if the
    date is already collected or the budget is spent.
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    date = date or now.date().isoformat()
    collected_at = now.replace(microsecond=0).isoformat()

    already = existing_snapshot_keys(store, date)
    if already and not force:
        raise AlreadyCollected(
            f"Clarity snapshot for {date} already exists ({len(already)} revision(s)). "
            "A second numOfDays=1 call today would cover an overlapping 24-hour "
            "window and must not become a second daily bucket. Use --force to store "
            "it as a non-authoritative revision."
        )

    validate_request(SNAPSHOT_NUM_DAYS, list(dimensions))

    budget = budget or ClarityCallBudget(store)
    budget.reserve(1, reason=f"daily snapshot {date}", now=now)

    session = session or requests.Session()
    payload = fetch_live_insights(session, token, SNAPSHOT_NUM_DAYS, list(dimensions))

    records = clarity_records(
        payload, date=date, collected_at=collected_at,
        window_end=collected_at, num_days=SNAPSHOT_NUM_DAYS,
    )
    kept, excluded, flags = assess_snapshot(records)

    # Raw first: if normalization has a bug, the payload is still preserved and
    # the facts layer can be rebuilt from it later.
    store.put_json(raw_key(CLARITY, date, collected_at), {
        "source": CLARITY,
        "date": date,
        "collected_at": collected_at,
        "window_days": SNAPSHOT_NUM_DAYS,
        "window_end": collected_at,
        "dimensions": list(dimensions),
        "is_daily_bucket": not already,
        "payload": payload,
    })

    if not already:
        store.put_records(facts_key(CLARITY, date), kept, overwrite=True)
        store.put_json(f"facts/{CLARITY}/{date}.quality.json", {
            "date": date,
            "collected_at": collected_at,
            "flags": [f.to_dict() for f in flags],
            "excluded_records": [r.to_dict() for r in excluded],
        }, overwrite=True)

    return {
        "date": date,
        "collected_at": collected_at,
        "api_calls_made": 1,
        "budget": budget.status(now=now),
        "records_stored": len(kept),
        "records_excluded": len(excluded),
        "is_daily_bucket": not already,
        "flags": flags,
        "metric_names": sorted({r.metric for r in kept}),
    }


def print_summary(summary, store):
    print("\n--- Clarity daily collection ---")
    print(f"  date:            {summary['date']} (UTC)")
    print(f"  window:          trailing 24h ending {summary['collected_at']}")
    print(f"  daily bucket:    {'yes' if summary['is_daily_bucket'] else 'no (extra revision)'}")
    print(f"  records stored:  {summary['records_stored']}")
    print(f"  records excluded:{summary['records_excluded']} (non-production)")
    budget = summary["budget"]
    print(f"  API calls:       1 this run; {budget['used']}/{budget['automated_cap']} "
          f"used today (Clarity hard limit {budget['hard_limit']}/project/day)")
    print(f"  storage:         {store.describe()}")

    if summary["flags"]:
        print("  data quality:")
        for flag in summary["flags"]:
            print(f"    [{flag.severity}] {flag.code}: {flag.message}")

    if not store.is_durable():
        print("\n  WARNING: this store is not durable. Snapshots written here do not")
        print("  survive an ephemeral CI runner. Clarity history cannot be backfilled,")
        print("  so wire a durable backend before relying on scheduled collection.")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Collect one non-overlapping Clarity daily snapshot (numOfDays=1) "
            "and store it. Makes exactly one API call."
        )
    )
    parser.add_argument("--store-root", default="analytics-data",
                        help="Directory for the local store (default: analytics-data)")
    parser.add_argument("--date", default=None,
                        help="UTC date to label the snapshot (default: today)")
    parser.add_argument("--force", action="store_true",
                        help="Store an extra revision for a date already collected. "
                             "The extra revision never becomes a daily bucket.")
    parser.add_argument("--automated-cap", type=int, default=None,
                        help="Override the automated per-day call cap (below Clarity's 10)")
    parser.add_argument("--status", action="store_true",
                        help="Report budget and stored coverage without calling the API")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    store = LocalFileStore(args.store_root)
    budget = (ClarityCallBudget(store, automated_cap=args.automated_cap)
              if args.automated_cap else ClarityCallBudget(store))

    if args.status:
        status = budget.status()
        collected = sorted({k.split("/")[2] for k in store.list_keys(raw_prefix(CLARITY))
                            if len(k.split("/")) > 2})
        print("Clarity collection status")
        print(f"  storage:        {store.describe()}")
        print(f"  days collected: {len(collected)}")
        if collected:
            print(f"  range:          {collected[0]} to {collected[-1]}")
        print(f"  budget today:   {status['used']}/{status['automated_cap']} used "
              f"(hard limit {status['hard_limit']})")
        return 0

    token = load_api_token()

    print("Molosoc — Clarity daily history collection")
    print("  auth:     CLARITY_API_TOKEN (bearer, never printed)")
    print("  mode:     read-only, single GET, numOfDays=1")

    try:
        summary = collect(store, token, budget=budget, date=args.date, force=args.force)
    except AlreadyCollected as exc:
        print(f"\nSkipped: {exc}")
        return 0
    except BudgetExhausted as exc:
        print(f"\nSkipped: {exc}")
        return 0
    except (StorageError, Exception) as exc:  # noqa: BLE001 — reported, redacted
        print(f"\nCollection failed: {describe_error(exc)}")
        return 1

    print_summary(summary, store)
    severity = worst_severity(summary["flags"])
    print(f"\nStored {summary['records_stored']} record(s) for {summary['date']} "
          f"(worst data-quality severity: {severity}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
