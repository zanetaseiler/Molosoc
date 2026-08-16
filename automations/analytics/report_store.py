#!/usr/bin/env python3
"""
Durable, agent-readable storage for the weekly marketing analysis report.

GitHub Actions artifacts expire after 90 days and can only be fetched by a
human with repository access holding a short-lived signed URL. That is a fine
download convenience and a poor foundation: a future strategy agent or
dashboard needs to answer "what is the newest report?" and "what happened in
March?" without listing a bucket or scraping the Actions API. This module makes
the existing private GCS bucket the durable machine-readable source, and leaves
the artifact exactly as it is.

LAYOUT

    reports/weekly/latest.json                      pointer, never expires
    reports/weekly/index.json                       index,   never expires
    reports/weekly/data/YYYY/MM/YYYY-MM-DD/report.json
    reports/weekly/data/YYYY/MM/YYYY-MM-DD/report.md
    reports/weekly/data/YYYY/MM/YYYY-MM-DD/revisions/<stamp>/report.{json,md}

The `data/` segment is the one deviation from the suggested layout, and it
exists for retention. GCS lifecycle conditions can match a prefix but cannot
express an exclusion, so any rule that expires `reports/weekly/` would take
`latest.json` and `index.json` with it. Putting the expiring reports under
their own prefix makes the eventual lifecycle rule a single safe line.

ORDER OF WRITES

The pointer is the last thing written and is never updated until both report
objects are stored and confirmed present. A reader that follows `latest.json`
therefore cannot land on a half-written report — the worst case is a pointer
one week stale, which is visibly old rather than quietly wrong.

MUTABLE POINTERS AND THE NARROW DELETE GRANT

`latest.json` and `index.json` are updated in place. GCS models replacing an
object as delete-then-create, so overwriting needs `storage.objects.delete` on
top of `storage.objects.create`, and the analytics writer was deliberately
scoped to create/get/list.

The grant is therefore conditional, not blanket: `storage.objects.delete` is
allowed only where `resource.name` is exactly one of the two objects in
MUTABLE_KEYS. Clarity history, dated reports and raw snapshots stay
undeletable by this identity — the guarantee Phase 1 was built on survives
intact, and the pointer still moves every week.

Until that condition is in place `publish()` degrades rather than losing
anything: the immutable report objects are already safe, the result says the
pointer is stale and names the exact grant needed, and `rebuild_pointers()`
reconstructs both mutable objects from a listing afterwards.

HISTORY SURVIVES RETENTION

Each index entry carries the week's headline numbers. The index is tiny
(~250 bytes per week, ~13 KB per year) and lives outside the expiring prefix,
so trend continuity outlives the full reports it points at.

No Clarity API call is made anywhere in this module. It reads and writes
storage only.
"""

import datetime as dt

from storage import PermissionDeniedError, StorageError

#: Bump the minor for additive fields, the major for anything a reader could
#: break on. Consumers should refuse a major they do not know.
SCHEMA_VERSION = "1.0.0"
REPORT_KIND = "molosoc.weekly_marketing_analysis"

ROOT = "reports/weekly"
DATA_ROOT = f"{ROOT}/data"
LATEST_KEY = f"{ROOT}/latest.json"
INDEX_KEY = f"{ROOT}/index.json"

#: The ONLY two objects this module ever overwrites.
#:
#: This tuple is not documentation — it is the contract the bucket's IAM
#: condition enforces. The analytics writer holds storage.objects.delete under
#: a condition matching exactly these two resource names, so an overwrite of
#: anything else is refused by GCS regardless of what the code asks for.
#: Clarity history, dated reports and raw snapshots are therefore
#: undeletable by this identity, which is the property the whole Phase 1
#: design rests on. A test asserts that publish() never overwrites a key
#: outside this tuple, so the code cannot drift outside the grant.
MUTABLE_KEYS = (LATEST_KEY, INDEX_KEY)

#: Recommended lifecycle for DATA_ROOT. Declared here and echoed into every
#: document so the intent is discoverable, but NOT applied — changing the
#: bucket lifecycle is a separate, approved action.
RETENTION_DAYS = 400
RETENTION_NOTE = (
    "Recommended lifecycle: delete objects under reports/weekly/data/ after "
    f"{RETENTION_DAYS} days. 400 rather than 365 so that a week can still be "
    "compared against the same week a year earlier — a 365-day rule deletes "
    "the comparison the week before it is needed. latest.json and index.json "
    "sit outside this prefix and are never expired. NOT YET APPLIED."
)

# Duplicate handling
ON_DUPLICATE_REJECT = "reject"
ON_DUPLICATE_REVISION = "revision"
ON_DUPLICATE_CHOICES = (ON_DUPLICATE_REJECT, ON_DUPLICATE_REVISION)

#: An index entry costs ~550 bytes, so a year is ~29 KB and three years ~90 KB
#: — one fetch, no pagination. The cap stops it growing without bound anyway:
#: beyond this, the oldest entries fold into a compact `archived` summary.
INDEX_MAX_ENTRIES = 260  # five years of weeks

#: Headline numbers copied into the index, so a year of trend survives the
#: reports themselves. Site-level only, and only metrics that always exist.
HEADLINE_METRICS = (
    "ga4_sessions",
    "ga4_users",
    "gsc_clicks",
    "gsc_impressions",
    "clarity_human_sessions",
)
SITE_ENTITY = "site"


class DuplicateReport(StorageError):
    """A report already exists for this week and the policy is to refuse."""


# --------------------------------------------------------------------------
# Key layout — one place that knows how reports are addressed
# --------------------------------------------------------------------------

def report_dir(report_date, revision=None):
    year, month = str(report_date)[:4], str(report_date)[5:7]
    base = f"{DATA_ROOT}/{year}/{month}/{report_date}"
    return f"{base}/revisions/{revision}" if revision else base


def report_key(report_date, extension="json", revision=None):
    return f"{report_dir(report_date, revision)}/report.{extension}"


def revision_stamp(now):
    """Sortable, filename-safe, and unique per generation instant."""
    return now.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# --------------------------------------------------------------------------
# The agent-readable document
# --------------------------------------------------------------------------

def headline_metrics(report):
    """Site-level totals, flat, for the index and for at-a-glance reading."""
    values = {}
    for fact in report.facts:
        if fact.entity_type == SITE_ENTITY and fact.metric in HEADLINE_METRICS:
            values[fact.metric] = fact.period_value
    return values


def build_document(report, markdown_key=None, json_key=None, revision=None):
    """Wrap the analysis object in the documented, versioned envelope.

    The analysis object already holds facts, inferences, anomalies and
    recommendations exactly once, with sections as ordered *references* into
    them. This adds the schema envelope and a `findings` map that names the
    views a future agent will ask for — also by reference, so naming a view
    costs a few bytes rather than a second copy that can drift.
    """
    document = report.to_dict()
    sections = document.get("sections", {})
    quality = document.get("data_quality", {})

    by_source = {}
    for fact in report.facts:
        by_source.setdefault(fact.source, []).append(fact.id)

    document["schema_version"] = SCHEMA_VERSION
    document["kind"] = REPORT_KIND
    document["report_date"] = report.as_of_date
    document["comparison_period"] = (report.comparison_periods or [None])[0]
    document["headline_metrics"] = headline_metrics(report)

    # Named views. Values are fact/inference/recommendation ids that resolve
    # against the flat collections above.
    document["findings"] = {
        "ga4": by_source.get("ga4", []),
        "search_console": by_source.get("gsc", []),
        "clarity": by_source.get("clarity", []),
        "seo": sections.get("seo_opportunities", {}),
        "landing_pages_and_cro": sections.get("landing_pages", {}),
        "ux": sections.get("clarity_ux", {}),
        "cross_source": sections.get("cross_source", {}),
        "executive_health": sections.get("executive_health", {}),
    }
    document["prioritized_actions"] = sections.get("prioritized_actions", [])

    # Promoted to the top level because every consumer needs them before it
    # can trust a number, and burying them one level down invites skipping.
    document["conversions"] = quality.get("conversions", {})
    document["ecommerce_tracking_boundary"] = quality.get("ecommerce_boundary", {})
    document["tracking_coverage"] = quality.get("tracking_coverage", {})
    document["source_coverage"] = document.get("data_coverage", {})

    document["storage"] = {
        "json_key": json_key or report_key(report.as_of_date, "json", revision),
        "markdown_key": markdown_key or report_key(report.as_of_date, "md", revision),
        "revision": revision,
        "retention": {
            "policy_applied": False,
            "recommended_days": RETENTION_DAYS,
            "expiring_prefix": f"{DATA_ROOT}/",
            "permanent_keys": [LATEST_KEY, INDEX_KEY],
            "note": RETENTION_NOTE,
        },
    }
    return document


def build_pointer(document, now):
    """The stable machine-readable `latest.json`.

    Deliberately small and flat: a consumer should be able to fetch this one
    object and know where to go next without parsing a report.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": f"{REPORT_KIND}.latest",
        "report_date": document["report_date"],
        "period": document["period"],
        "comparison_period": document["comparison_period"],
        "json_key": document["storage"]["json_key"],
        "markdown_key": document["storage"]["markdown_key"],
        "readiness": document["readiness"],
        "readiness_note": document.get("readiness_note", ""),
        "generated_at": document["generated_at"],
        "pointer_updated_at": now.replace(microsecond=0).isoformat(),
        "report_id": document.get("report_id"),
        "index_key": INDEX_KEY,
    }


def build_index_entry(document, revisions=0):
    """One line of history. Kept small on purpose — this outlives the report."""
    counts = {}
    for rec in document.get("recommendations", []):
        counts[rec["priority"]] = counts.get(rec["priority"], 0) + 1
    return {
        "report_date": document["report_date"],
        "period_start": document["period"]["start"],
        "period_end": document["period"]["end"],
        "comparison_start": (document["comparison_period"] or {}).get("start"),
        "comparison_end": (document["comparison_period"] or {}).get("end"),
        "readiness": document["readiness"],
        "json_key": document["storage"]["json_key"],
        "markdown_key": document["storage"]["markdown_key"],
        "generated_at": document["generated_at"],
        "recommendation_counts": counts,
        "headline_metrics": document.get("headline_metrics", {}),
        "conversion_state": (document.get("conversions") or {}).get("state"),
        "revisions": revisions,
    }


def empty_index(now=None):
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": f"{REPORT_KIND}.index",
        "updated_at": (now or _utc_now()).replace(microsecond=0).isoformat(),
        "count": 0,
        "entries": [],
        "retention": {
            "policy_applied": False,
            "recommended_days": RETENTION_DAYS,
            "expiring_prefix": f"{DATA_ROOT}/",
            "note": RETENTION_NOTE,
        },
    }


def upsert_entry(index, entry, now=None):
    """Newest first. Re-publishing a week replaces its line, never appends."""
    entries = [e for e in index.get("entries", [])
               if e.get("report_date") != entry["report_date"]]
    entries.append(entry)
    entries.sort(key=lambda e: e.get("report_date", ""), reverse=True)

    if len(entries) > INDEX_MAX_ENTRIES:
        dropped, entries = entries[INDEX_MAX_ENTRIES:], entries[:INDEX_MAX_ENTRIES]
        archived = index.get("archived") or {"count": 0, "earliest_report_date": None}
        archived["count"] += len(dropped)
        earliest = min(e["report_date"] for e in dropped)
        archived["earliest_report_date"] = min(
            filter(None, [archived.get("earliest_report_date"), earliest]))
        archived["latest_archived_report_date"] = max(
            e["report_date"] for e in dropped)
        archived["note"] = (
            "Older weeks are summarised here to keep the index one small fetch. "
            "Their reports, if still within retention, remain at "
            f"{DATA_ROOT}/YYYY/MM/YYYY-MM-DD/report.json and can be listed directly."
        )
        index["archived"] = archived

    index["entries"] = entries
    index["count"] = len(entries)
    index["updated_at"] = (now or _utc_now()).replace(microsecond=0).isoformat()
    index["schema_version"] = SCHEMA_VERSION
    return index


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------

def load_latest(store):
    """The newest complete report's pointer, or None if nothing is published."""
    try:
        return store.get_json(LATEST_KEY)
    except StorageError:
        return None


def load_index(store):
    try:
        return store.get_json(INDEX_KEY)
    except StorageError:
        return None


def load_report(store, report_date=None):
    """Fetch a report document — the newest by default, or a named week."""
    if report_date is None:
        pointer = load_latest(store)
        if not pointer:
            raise StorageError(
                f"no {LATEST_KEY} in this store; nothing has been published yet"
            )
        return store.get_json(pointer["json_key"])
    return store.get_json(report_key(report_date, "json"))


def published_dates(store):
    """Every published week, newest first, straight from the object listing.

    The index is the cheap path; this is the authoritative one, and what
    rebuild_pointers() uses when the index is missing or stale.
    """
    dates = set()
    for key in store.list_keys(f"{DATA_ROOT}/"):
        parts = key.split("/")
        # reports/weekly/data/YYYY/MM/YYYY-MM-DD/report.json
        if len(parts) == 7 and parts[-1] == "report.json":
            dates.add(parts[5])
    return sorted(dates, reverse=True)


def count_revisions(store, report_date):
    prefix = f"{report_dir(report_date)}/revisions/"
    stamps = {k[len(prefix):].split("/")[0] for k in store.list_keys(prefix)}
    return len(stamps)


# --------------------------------------------------------------------------
# Publishing
# --------------------------------------------------------------------------

class PublishResult:
    """What actually happened, in enough detail to act on.

    `stored` is the fact that matters: it is True only when both immutable
    report objects are in the bucket. `pointer_updated` being False alongside
    `stored` being True is the degraded-but-safe case.
    """

    def __init__(self, report_date, json_key, markdown_key, revision=None):
        self.report_date = report_date
        self.json_key = json_key
        self.markdown_key = markdown_key
        self.revision = revision
        self.stored = False
        self.pointer_updated = False
        self.index_updated = False
        self.pointer_error = None
        self.skipped_duplicate = False
        self.latest_unchanged_reason = None

    @property
    def degraded(self):
        return self.stored and not (self.pointer_updated and self.index_updated)

    def to_dict(self):
        return {
            "report_date": self.report_date,
            "json_key": self.json_key,
            "markdown_key": self.markdown_key,
            "revision": self.revision,
            "stored": self.stored,
            "pointer_updated": self.pointer_updated,
            "index_updated": self.index_updated,
            "pointer_error": self.pointer_error,
            "skipped_duplicate": self.skipped_duplicate,
            "latest_unchanged_reason": self.latest_unchanged_reason,
            "degraded": self.degraded,
        }


def publish(store, report, markdown, now=None, on_duplicate=ON_DUPLICATE_REJECT):
    """Store one weekly report durably, then move the pointer.

    Raises DuplicateReport when the week already exists and the policy is to
    refuse. Never overwrites an authoritative report under any policy.
    """
    if on_duplicate not in ON_DUPLICATE_CHOICES:
        raise ValueError(f"unknown duplicate policy: {on_duplicate!r}")

    now = now or _utc_now()
    report_date = report.as_of_date
    revision = None

    if store.exists(report_key(report_date, "json")):
        if on_duplicate == ON_DUPLICATE_REJECT:
            raise DuplicateReport(
                f"a report for {report_date} is already published at "
                f"{report_key(report_date, 'json')}. The authoritative record for a "
                "week is written once. Re-run with the revision policy to file this "
                "run alongside it without replacing it."
            )
        revision = revision_stamp(now)

    json_key = report_key(report_date, "json", revision)
    markdown_key = report_key(report_date, "md", revision)
    result = PublishResult(report_date, json_key, markdown_key, revision)

    document = build_document(report, markdown_key=markdown_key,
                              json_key=json_key, revision=revision)

    # Immutable writes first, create-if-absent. Markdown before JSON so the
    # JSON — the object the pointer names — is the last to appear.
    store.put_text(markdown_key, markdown, content_type="text/markdown")
    store.put_json(json_key, document)

    if not (store.exists(json_key) and store.exists(markdown_key)):
        raise StorageError(
            f"report objects for {report_date} did not appear after writing; "
            "refusing to move the pointer to a report that may be incomplete"
        )
    result.stored = True

    # Only now, with both objects confirmed present, touch the mutable state.
    _update_index(store, document, result, now)
    _update_latest(store, document, result, now)
    return result


def _update_index(store, document, result, now):
    index = load_index(store) or empty_index(now)
    revisions = count_revisions(store, document["report_date"])
    upsert_entry(index, build_index_entry(document, revisions), now)
    try:
        store.put_json(INDEX_KEY, index, overwrite=True)
        result.index_updated = True
    except PermissionDeniedError as exc:
        result.pointer_error = str(exc)
    except StorageError as exc:
        result.pointer_error = str(exc)


def _update_latest(store, document, result, now):
    current = load_latest(store)
    if current and current.get("report_date", "") > document["report_date"]:
        # An older week was re-run. `latest` means newest, not most recently
        # written, so it stays where it is.
        result.latest_unchanged_reason = (
            f"latest already points at {current['report_date']}, which is newer "
            f"than {document['report_date']}"
        )
        result.pointer_updated = True
        return
    try:
        store.put_json(LATEST_KEY, build_pointer(document, now), overwrite=True)
        result.pointer_updated = True
    except PermissionDeniedError as exc:
        result.pointer_error = str(exc)
    except StorageError as exc:
        result.pointer_error = str(exc)


def rebuild_pointers(store, now=None):
    """Reconstruct `index.json` and `latest.json` from the stored reports.

    The recovery path for pointer writes that were skipped — after a
    permission gap, an interrupted run, or a manual upload. Reads every
    published report once, so it is the expensive path, not the weekly one.
    """
    now = now or _utc_now()
    index = empty_index(now)
    newest_document = None

    for report_date in reversed(published_dates(store)):
        document = store.get_json(report_key(report_date, "json"))
        upsert_entry(index, build_index_entry(
            document, count_revisions(store, report_date)), now)
        newest_document = document

    store.put_json(INDEX_KEY, index, overwrite=True)
    if newest_document is not None:
        store.put_json(LATEST_KEY, build_pointer(newest_document, now), overwrite=True)
    return index


def _utc_now():
    return dt.datetime.now(dt.timezone.utc)
