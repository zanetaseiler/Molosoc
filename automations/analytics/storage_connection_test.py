#!/usr/bin/env python3
"""
Molosoc analytics: connection test for the GCS durable storage backend.

Proves ANALYTICS_STORAGE_SA_JSON + ANALYTICS_BUCKET actually reach the real
bucket, using one synthetic object — never real Clarity/GA4/GSC data, and no
Clarity API call is made anywhere in this script.

Checks, against the real bucket:
  1. write one synthetic object (create-if-absent)
  2. read it back and confirm the content matches exactly
  3. list it and confirm it appears
  4. write the SAME key again and confirm it is correctly refused — this is
     the create-if-absent protection that keeps a re-run from silently
     clobbering a day of Clarity history

The synthetic object is deliberately NOT deleted afterward: the writer
service account was scoped to create/get/list only, with no delete, so this
script has no way to clean up after itself even if it wanted to. That's a
direct consequence of the least-privilege role, not an oversight — cleanup of
`_verification/` objects is a separate, manual action for whoever holds
broader permissions.

Usage:
    export ANALYTICS_STORAGE_SA_JSON='...'
    export ANALYTICS_BUCKET='molosoc-analytics-history'
    python3 automations/analytics/storage_connection_test.py

Exit code is 0 only when all four checks pass against the real bucket.
"""

import datetime as dt
import json
import sys

from analytics_common import redact
from storage import StorageError
from storage_gcs import store_from_env


def main(argv=None):
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"_verification/synthetic-{timestamp}.json"
    payload = {
        "type": "synthetic_verification",
        "note": "Phase 1 storage wiring check. No Clarity API call was made.",
        "timestamp": timestamp,
    }

    try:
        store = store_from_env()
    except Exception as exc:  # noqa: BLE001 — incl. auth-layer errors, redacted
        print(f"FAIL setup: {redact(exc)}", file=sys.stderr)
        return 1

    print(f"Store: {store.describe()}")

    # 1. Write (create-if-absent)
    try:
        store.put_json(key, payload)
    except StorageError as exc:
        print(f"FAIL write: {redact(exc)}", file=sys.stderr)
        return 1
    print(f"PASS write: {key}")

    # 2. Read back and compare
    try:
        read_back = store.get_json(key)
    except StorageError as exc:
        print(f"FAIL read: {redact(exc)}", file=sys.stderr)
        return 1
    if read_back != payload:
        print(f"FAIL read: content mismatch\n  wrote: {json.dumps(payload)}\n  read:  {json.dumps(read_back)}",
              file=sys.stderr)
        return 1
    print("PASS read: content matches exactly")

    # 3. List
    try:
        names = store.list_keys("_verification/")
    except StorageError as exc:
        print(f"FAIL list: {redact(exc)}", file=sys.stderr)
        return 1
    if key not in names:
        print(f"FAIL list: {key} not found under _verification/ (saw {len(names)} object(s))",
              file=sys.stderr)
        return 1
    print(f"PASS list: object present ({len(names)} object(s) under _verification/)")

    # 4. Create-if-absent protection, against the real bucket
    try:
        store.put_json(key, {"attempt": "second write, same key"})
        print("FAIL create-if-absent: second write to the same key was NOT rejected",
              file=sys.stderr)
        return 1
    except StorageError as exc:
        if "already exists" not in str(exc):
            print(f"FAIL create-if-absent: rejected, but not for the expected reason: {redact(exc)}",
                  file=sys.stderr)
            return 1
        print("PASS create-if-absent: second write to the same key was correctly refused")

    print(f"\nAll checks passed. Synthetic object left in place at:\n  {key}")
    print("(not deleted — the writer service account has no delete permission)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
