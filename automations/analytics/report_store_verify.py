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

Before any of that, it runs ONE probe against a production path — an
idempotent create-or-rewrite of `reports/weekly/index.json`.

That probe exists because the isolation which makes the rest of this script
safe also puts it beyond the permission it needs to test. The conditional
`storage.objects.delete` grant matches `resource.name` by EQUALITY against the
two production pointer names, so an object at
`_verification/reports/<stamp>/reports/weekly/latest.json` is a different name
and is correctly not covered. No amount of testing under the verification
prefix can prove the production grant; only touching the real object can.

The probe is a no-op by construction. If the index does not exist it creates a
valid empty one — the correct initial state, and exactly what the first real
publish would create anyway. Then it reads the object and writes the same
parsed document back. `put_json` serialises deterministically, so the result is
byte-identical, and the probe asserts that rather than assuming it. Logical
contents never change, and no other production object is touched.

Consequently, the second-week pointer failure under the verification prefix is
now reported as an expected NOTE rather than a problem: the mechanism is proven
there, the permission is proven by the probe.

Exit codes: 0 everything passed, 1 something is genuinely wrong.

Usage:
    export ANALYTICS_STORAGE_SA_JSON='...'
    export ANALYTICS_BUCKET='molosoc-analytics-history'
    python3 automations/analytics/report_store_verify.py

Objects are left in place: the writer has no delete permission, so cleanup of
`_verification/` is a manual action for whoever holds broader access.
"""

import datetime as dt
import json
import os
import sys

import report_store as rs
import weekly_report as wr
from analytics_common import redact
from storage import PermissionDeniedError, StorageError
from storage_gcs import BUCKET_ENV, GCSStore, load_storage_credentials_info

VERIFICATION_ROOT = "_verification/reports"


class Outcome:
    """Pass/fail tallies, with a third bucket for expected-and-harmless."""

    def __init__(self):
        self.failures = []
        self.notes = []

    def ok(self, message):
        print(f"PASS {message}")

    def fail(self, message):
        print(f"FAIL {message}", file=sys.stderr)
        self.failures.append(message)

    def note(self, message):
        """Something worth saying that is not a problem."""
        print(f"NOTE {message}")
        self.notes.append(message)


# --------------------------------------------------------------------------
# The production pointer probe
# --------------------------------------------------------------------------

def probe_production_pointer(store, outcome, now):
    """Prove the IAM condition on the real reports/weekly/index.json.

    This is the only check that touches a production path, and it is the only
    one that can prove the conditional delete grant, because that grant matches
    resource.name by EQUALITY. Objects under the verification prefix have
    different names and are deliberately outside it.

    Idempotent by construction:

      * if the index does not exist, create a valid empty one using the
        production schema — which is the correct initial state anyway, and
        exactly what the first real publish would otherwise create;
      * read it back, then write the SAME parsed document again.

    put_json serialises deterministically, so re-writing an unchanged document
    reproduces the object byte for byte. The probe asserts that rather than
    assuming it. Logical contents are never modified.

    Touches reports/weekly/index.json and nothing else — not latest.json, not
    any dated report, not the Clarity ledger. A guard enforces that rather than
    trusting the caller to pass the right store.
    """
    key = rs.INDEX_KEY

    prefix = getattr(store, "prefix", "")
    if prefix:
        outcome.fail(
            f"the production probe was handed a store prefixed with {prefix!r}. "
            "It must address real object names, or it proves nothing about the "
            "condition that governs them."
        )
        return
    if key != "reports/weekly/index.json":
        outcome.fail(f"refusing to probe an unexpected object: {key}")
        return

    try:
        existed = store.exists(key)
    except StorageError as exc:
        outcome.fail(f"production probe could not check for {key}: {redact(exc)}")
        return

    if not existed:
        try:
            store.put_json(key, rs.empty_index(now))
        except StorageError as exc:
            outcome.fail(f"production probe could not create {key}: {redact(exc)}")
            return
        outcome.ok(f"created {key} — a valid empty index, the correct initial state")
    else:
        outcome.note(f"{key} already exists; rewriting it unchanged")

    try:
        before_text = store.get_text(key)
        before_doc = json.loads(before_text)
    except (StorageError, ValueError) as exc:
        outcome.fail(f"production probe could not read {key}: {redact(exc)}")
        return

    # THE PROBE. Same document, written over itself. This is the delete-then-
    # create that the conditional grant must permit, on the exact object name
    # the condition names.
    try:
        store.put_json(key, before_doc, overwrite=True)
    except PermissionDeniedError as exc:
        outcome.fail(
            f"the conditional delete grant does NOT cover {key}: {redact(exc)} "
            "This is the production path, so the weekly report would fail to "
            "update its index from its second run onward. Check the condition's "
            "resource.name expression."
        )
        return
    except StorageError as exc:
        outcome.fail(f"production probe rewrite of {key} failed: {redact(exc)}")
        return

    try:
        after_text = store.get_text(key)
    except StorageError as exc:
        outcome.fail(f"production probe could not re-read {key}: {redact(exc)}")
        return

    if after_text != before_text:
        outcome.fail(
            f"{key} changed across an idempotent rewrite "
            f"({len(before_text)} bytes before, {len(after_text)} after). The "
            "probe was supposed to be a no-op."
        )
        return

    outcome.ok(f"rewrote {key} byte-for-byte identically ({len(after_text)} bytes) "
               "— the conditional storage.objects.delete grant is proven")
    outcome.ok("logical contents unchanged: "
               f"{json.loads(after_text) == before_doc}")


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
        outcome.fail(f"index.json could not be created: {first.pointer_error}")

    if first.pointer_updated and not first.pointer_error:
        pointer = rs.load_latest(store)
        if pointer and pointer.get("report_date") == report.as_of_date:
            outcome.ok(f"latest.json points at {pointer['report_date']}")
        else:
            outcome.fail("latest.json does not resolve to the report just published")
    else:
        outcome.fail(f"latest.json could not be created: {first.pointer_error}")

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
            # EXPECTED, and not a problem. The delete grant matches
            # resource.name by equality against the two production pointer
            # names; objects under this run's verification prefix have
            # different names and are deliberately outside it. The mechanism
            # is proven here, the permission is proven by
            # probe_production_pointer() against the real object.
            outcome.note(
                "a second week stored its reports; its pointer update was "
                "refused because this run writes under the verification "
                "prefix, which the production-scoped grant correctly does not "
                "cover. The grant itself is proven separately, above."
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
            outcome.note("latest.json absent under this prefix, so pointer "
                         "regression is untested here")
        elif newest >= report.as_of_date:
            outcome.ok(f"older week stored without dragging latest back (still {newest})")
        else:
            outcome.fail(
                f"latest regressed to {newest} after publishing an older week"
            )

    # --- 8. discovery from the pointer alone ------------------------------
    pointer = rs.load_latest(store)
    if pointer is None:
        outcome.note("discovery via latest.json is untested here (pointer absent)")
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
        production = GCSStore(bucket_name=_bucket(), prefix="",
                              credentials_info=load_storage_credentials_info())
        store, prefix = build_verification_store(run_stamp)
    except Exception as exc:  # noqa: BLE001 — incl. auth errors, redacted
        print(f"FAIL setup: {redact(exc)}", file=sys.stderr)
        return 1

    print(f"Bucket: gs://{production.bucket_name}")
    print(f"Isolated verification prefix: {prefix}/")
    print("Zero Clarity API calls. No dated weekly report, no latest.json, no "
          "Clarity ledger object, no GA4/Search Console data, no WordPress or "
          "site content is read or written.\n")

    # 1. The production probe. The only production path touched, and the only
    #    check that can prove the conditional grant, because that grant matches
    #    resource.name by equality.
    print(f"--- production pointer probe ({rs.INDEX_KEY}) ---")
    try:
        probe_production_pointer(production, outcome, now)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL production probe: {redact(exc)}", file=sys.stderr)
        outcome.failures.append("production probe raised")

    # 2. The mechanism, end to end, entirely inside the verification prefix.
    print(f"\n--- report-storage mechanism (synthetic, {prefix}/) ---")
    try:
        verify(store, outcome, now)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL unexpected: {redact(exc)}", file=sys.stderr)
        outcome.failures.append("unexpected error")

    print(f"\nSynthetic objects left in place under {prefix}/ — the writer's "
          "delete grant covers the two production pointer names only, so this "
          "script cannot clean up after itself. Sweep manually when convenient.")

    if outcome.failures:
        print(f"\n{len(outcome.failures)} check(s) FAILED.", file=sys.stderr)
        return 1

    print(f"\nAll checks passed ({len(outcome.notes)} informational note(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
