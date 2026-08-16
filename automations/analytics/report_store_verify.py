#!/usr/bin/env python3
"""
Live verification of the report-storage mechanism against the real bucket.

Everything happens under an isolated prefix — `_verification/reports/...` — so
no real weekly report, no Clarity ledger object, and no existing analytics
history is read, written, overwritten, or deleted. The reports published here
are built from the offline fixtures, never from live data.

NO CLARITY API CALL IS MADE. This script does not import clarity_api, and the
fixture reports it publishes come from stored records only.

What it proves against the real bucket:

  1. a first weekly report writes both objects (Markdown + JSON)
  2. the index is created and lists that week
  3. the latest pointer is created and resolves back to the report
  4. republishing the same week is refused (the historical record is safe)
  5. the revision policy files a re-run alongside the original, and the
     authoritative report.json is byte-for-byte unchanged
  6. a second week UPDATES the pointer in place — not merely creates it
  7. an older week does not drag the latest pointer backwards
  8. a report can be discovered from the pointer alone, with no bucket listing

Check 6 is the one that earns its keep. The verification prefix is fresh on
every run, so writing `latest.json` the first time is a create and needs only
`storage.objects.create`. Production replaces that object every week, and
replacing needs `storage.objects.delete` as well, because GCS implements
"replace an object" as delete-then-create. A verification that stopped at
check 3 would pass against a create-only writer while the weekly job failed
from its second run onward.

Where that permission is missing the script reports NEEDS-PERMISSION with the
exact grant required rather than a failure: the immutable half is what proves
the reports are durable, and that half stands on its own.

Usage:
    export ANALYTICS_STORAGE_SA_JSON='...'
    export ANALYTICS_BUCKET='molosoc-analytics-history'
    python3 automations/analytics/report_store_verify.py

Objects are left in place: the writer has no delete permission, so cleanup of
`_verification/` is a manual action for whoever holds broader access.
"""

import datetime as dt
import os
import sys

import report_store as rs
import weekly_report as wr
from analytics_common import redact
from storage import StorageError
from storage_gcs import BUCKET_ENV, GCSStore, load_storage_credentials_info

VERIFICATION_ROOT = "_verification/reports"


class Outcome:
    """Pass/fail tallies that keep a permission gap distinct from a break."""

    def __init__(self):
        self.failures = []
        self.needs_permission = []

    def ok(self, message):
        print(f"PASS {message}")

    def fail(self, message):
        print(f"FAIL {message}", file=sys.stderr)
        self.failures.append(message)

    def permission(self, message):
        print(f"NEEDS-PERMISSION {message}", file=sys.stderr)
        self.needs_permission.append(message)


def build_verification_store(run_stamp):
    """A store rooted at an isolated, run-unique prefix.

    Run-unique so a second verification cannot collide with the first, and so
    the create-if-absent checks below are testing this run's writes rather
    than yesterday's leftovers.
    """
    prefix = f"{VERIFICATION_ROOT}/{run_stamp}"
    return GCSStore(
        bucket_name=_bucket(),
        prefix=prefix,
        credentials_info=load_storage_credentials_info(),
    ), prefix


def _bucket():
    bucket = os.environ.get(BUCKET_ENV, "").strip()
    if not bucket:
        raise StorageError(f"{BUCKET_ENV} is not set.")
    return bucket


def fixture_report(scenario, today):
    """A complete analysis object from fixture data. No network, no Clarity."""
    return wr.generate_from_fixture(scenario, today=today)


def verify(store, outcome, now):
    # --- 1. first write ---------------------------------------------------
    report, markdown = fixture_report("low_volume", "2026-08-17")
    try:
        first = rs.publish(store, report, markdown, now=now)
    except StorageError as exc:
        outcome.fail(f"first publish: {redact(exc)}")
        return

    if not first.stored:
        outcome.fail("first publish: reports were not stored")
        return
    outcome.ok(f"first publish stored {first.json_key} and {first.markdown_key}")

    # Read both back and confirm the content survived the round trip.
    try:
        stored_doc = store.get_json(first.json_key)
        stored_md = store.get_text(first.markdown_key)
    except StorageError as exc:
        outcome.fail(f"read back: {redact(exc)}")
        return
    if stored_md != markdown:
        outcome.fail("read back: Markdown does not match what was written")
    elif stored_doc.get("schema_version") != rs.SCHEMA_VERSION:
        outcome.fail(f"read back: schema_version is {stored_doc.get('schema_version')!r}")
    else:
        outcome.ok(f"read back matches exactly (schema {rs.SCHEMA_VERSION})")

    # --- 2/3. index and pointer ------------------------------------------
    if first.index_updated:
        index = rs.load_index(store)
        dates = [e["report_date"] for e in (index or {}).get("entries", [])]
        if report.as_of_date in dates:
            outcome.ok(f"index lists {report.as_of_date} ({len(dates)} entry/entries)")
        else:
            outcome.fail(f"index does not list {report.as_of_date}")
    else:
        outcome.permission(f"index.json could not be written: {first.pointer_error}")

    if first.pointer_updated and not first.pointer_error:
        pointer = rs.load_latest(store)
        if pointer and pointer.get("report_date") == report.as_of_date:
            outcome.ok(f"latest.json points at {pointer['report_date']}")
        else:
            outcome.fail("latest.json does not resolve to the report just published")
    else:
        outcome.permission(f"latest.json could not be written: {first.pointer_error}")

    # --- 4. duplicate refused --------------------------------------------
    try:
        rs.publish(store, report, markdown, now=now)
        outcome.fail("duplicate publish was NOT refused — history is overwritable")
    except rs.DuplicateReport:
        outcome.ok("duplicate publish for the same week was correctly refused")
    except StorageError as exc:
        outcome.fail(f"duplicate publish failed for the wrong reason: {redact(exc)}")

    # --- 5. revision policy preserves the original ------------------------
    before = store.get_json(first.json_key)
    try:
        revised = rs.publish(store, report, markdown, now=now + dt.timedelta(minutes=5),
                             on_duplicate=rs.ON_DUPLICATE_REVISION)
    except StorageError as exc:
        outcome.fail(f"revision publish: {redact(exc)}")
        revised = None

    if revised and revised.stored and revised.revision:
        after = store.get_json(first.json_key)
        if after != before:
            outcome.fail("revision publish MODIFIED the authoritative report")
        elif not store.exists(revised.json_key):
            outcome.fail(f"revision publish did not store {revised.json_key}")
        else:
            outcome.ok(f"revision filed at {revised.json_key}; original untouched")

    # --- 6. the pointer can be UPDATED, not merely created ----------------
    # This is the check that matters against a create-only writer. The
    # verification prefix is fresh each run, so the first latest.json is a
    # create and needs no delete permission; only publishing a second week
    # exercises the replace that production performs every single week.
    newer, newer_md = fixture_report("low_volume", "2026-08-24")
    try:
        second = rs.publish(store, newer, newer_md, now=now)
    except StorageError as exc:
        outcome.fail(f"second-week publish: {redact(exc)}")
        second = None

    if second and second.stored:
        if second.degraded:
            outcome.permission(
                "a second week stored its reports but could not update "
                f"latest.json/index.json: {second.pointer_error}"
            )
        else:
            pointer = rs.load_latest(store)
            if pointer and pointer.get("report_date") == newer.as_of_date:
                outcome.ok(f"latest.json updated in place to {newer.as_of_date} "
                           "— the weekly replace works")
            else:
                outcome.fail("second week did not move latest.json")

    # --- 7. latest never moves backwards ----------------------------------
    older, older_md = fixture_report("low_volume", "2026-08-10")
    try:
        older_result = rs.publish(store, older, older_md, now=now)
    except StorageError as exc:
        outcome.fail(f"older-week publish: {redact(exc)}")
        older_result = None

    if older_result and older_result.stored:
        pointer = rs.load_latest(store)
        newest = (pointer or {}).get("report_date")
        if pointer is None:
            outcome.permission("latest.json absent, so pointer regression is untested")
        elif newest >= report.as_of_date:
            outcome.ok(f"older week stored without dragging latest back (still {newest})")
        else:
            outcome.fail(
                f"latest regressed to {newest} after publishing an older week"
            )

    # --- 8. discovery from the pointer alone ------------------------------
    pointer = rs.load_latest(store)
    if pointer is None:
        outcome.permission("discovery via latest.json is untested (pointer absent)")
    else:
        try:
            document = store.get_json(pointer["json_key"])
            markdown_back = store.get_text(pointer["markdown_key"])
        except StorageError as exc:
            outcome.fail(f"discovery from pointer: {redact(exc)}")
        else:
            if document.get("report_date") == pointer["report_date"] and markdown_back:
                outcome.ok("a consumer can reach the newest report from latest.json "
                           "alone, with no bucket listing")
            else:
                outcome.fail("pointer resolved to a report that does not match it")


def main(argv=None):
    now = dt.datetime.now(dt.timezone.utc)
    run_stamp = now.strftime("%Y%m%dT%H%M%SZ")
    outcome = Outcome()

    try:
        store, prefix = build_verification_store(run_stamp)
    except Exception as exc:  # noqa: BLE001 — incl. auth errors, redacted
        print(f"FAIL setup: {redact(exc)}", file=sys.stderr)
        return 1

    print(f"Store: {store.describe()}")
    print(f"Isolated verification prefix: {prefix}/")
    print("No real weekly report, Clarity ledger object, or analytics history "
          "is touched. Zero Clarity API calls.\n")

    try:
        verify(store, outcome, now)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL unexpected: {redact(exc)}", file=sys.stderr)
        outcome.failures.append("unexpected error")

    print(f"\nObjects left in place under {prefix}/ "
          "(the writer has no delete permission).")

    if outcome.failures:
        print(f"\n{len(outcome.failures)} check(s) FAILED.", file=sys.stderr)
        return 1
    if outcome.needs_permission:
        print(f"\nImmutable report storage verified. "
              f"{len(outcome.needs_permission)} check(s) need a permission the "
              "writer does not have:\n"
              "  storage.objects.delete on this bucket (GCS implements object "
              "replacement as delete-then-create).\n"
              "  Without it, reports are stored durably but latest.json and "
              "index.json cannot be updated.", file=sys.stderr)
        return 2

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
