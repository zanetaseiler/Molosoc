#!/usr/bin/env python3
"""
Where `marketing_intelligence.json` lives, and how it gets there.

It sits beside the report it was derived from:

    reports/weekly/data/{YYYY}/{MM}/{YYYY-MM-DD}/report.json
    reports/weekly/data/{YYYY}/{MM}/{YYYY-MM-DD}/marketing_intelligence.json

That location is derived from `report_store.report_dir`, not spelled out
again here, so the two can never drift apart. Three things follow from it for
free: the object inherits the same create-once immutability as the report, it
falls under the `data/` prefix the retention rule already covers, and it needs
**no IAM change** — the writer can already create objects in that prefix.

No new pointer. A `marketing_intelligence_latest.json` would have to be
mutable, which would mean extending the narrowly-scoped delete grant to a
third object. A consumer instead reads the existing `reports/weekly/latest.json`
and swaps the filename on `json_key`; `key_for_report_key` below is that swap,
so a consumer never has to reconstruct the path from parts.
"""

import json

import report_store as rs
from storage import StorageError

FILENAME = "marketing_intelligence.json"


def key_for(report_date, revision=None):
    """Derived from the report's own directory — never composed separately."""
    return f"{rs.report_dir(report_date, revision)}/{FILENAME}"


def key_for_report_key(report_json_key):
    """The sibling of a report key. This is how a consumer finds it.

    `latest.json` carries `json_key`; swapping the filename is the whole
    lookup, which is why no second pointer had to be created and no mutable
    object had to be added to the delete grant.
    """
    head, _, tail = str(report_json_key).rpartition("/")
    if not head or not tail:
        raise ValueError(f"not a report key: {report_json_key!r}")
    return f"{head}/{FILENAME}"


class AlreadyPublished(StorageError):
    """An intelligence document already exists for this week."""


def load_report(store, report_date):
    """The stored weekly report — the canonical envelope, not a local copy."""
    key = rs.report_key(report_date, "json")
    try:
        return json.loads(store.get_text(key)), key
    except StorageError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise StorageError(f"could not read {key}: {exc}") from None


def publish(store, document, report_date, overwrite=False):
    """Write it once. A second run for the same week is refused by default.

    Same policy as the report it sits beside, and for the same reason: the
    interpretation of a given week is part of the historical record, and a
    re-run that quietly replaced it would make the record depend on when it
    was last looked at.
    """
    key = key_for(report_date)
    if not overwrite and store.exists(key):
        raise AlreadyPublished(
            f"{key} already exists. The interpretation for this week is "
            "already published and was left untouched.")
    store.put_text(key, json.dumps(document, indent=2, ensure_ascii=False),
                   overwrite=overwrite, content_type="application/json")
    return key
