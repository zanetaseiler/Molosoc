#!/usr/bin/env python3
"""
Offline tests for durable, agent-readable report storage.

The properties that matter, and why:

  1. A published week is never silently overwritten. The weekly report is the
     only record of what the site looked like that week; a re-run that
     replaced it would destroy evidence that cannot be regenerated once
     Search Console's window has rolled past.
  2. `latest.json` is never updated until both report objects are confirmed
     stored. A consumer that follows the pointer must not be able to land on
     half a report.
  3. A pointer write that is refused for lack of permission degrades — reports
     stay stored, the caller is told, and nothing is lost.
  4. Everything stays offline: zero Clarity API calls, nothing written to Git.

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import clarity_api  # noqa: E402
import report_store as rs  # noqa: E402
import weekly_report as wr  # noqa: E402
from analysis_model import INSUFFICIENT_DATA, PRIORITY_MONITOR, READY  # noqa: E402
from storage import InMemoryStore, PermissionDeniedError, StorageError  # noqa: E402

NOW = dt.datetime(2026, 8, 17, 6, 0, tzinfo=dt.timezone.utc)


@pytest.fixture(autouse=True)
def no_live_clarity(monkeypatch):
    """Any live Clarity call fails every test in this file, loudly."""
    def forbidden(*_args, **_kwargs):
        raise AssertionError(
            "report storage must never call the Clarity API — it reads and "
            "writes storage only"
        )

    monkeypatch.setattr(clarity_api, "fetch_live_insights", forbidden)
    monkeypatch.setattr(clarity_api, "load_api_token", forbidden)


@pytest.fixture
def store():
    return InMemoryStore()


def make_report(scenario="low_volume", today="2026-08-17"):
    return wr.generate_from_fixture(scenario, today=today)


class DenyOverwriteStore(InMemoryStore):
    """A writer scoped to create/get/list, like the real analytics identity.

    GCS implements replacing an object as delete-then-create, so an identity
    without storage.objects.delete can create an object but not replace one.
    Modelled precisely: creating latest.json the first time succeeds, and
    every update from the second week onward is refused. A stub that refused
    the first write too would make the first week look broken and — worse —
    let a live check against a fresh prefix pass while production failed.
    """

    def put_json(self, key, document, overwrite=False):
        if overwrite and key in self._data:
            raise PermissionDeniedError(
                f"overwrite of {key} was denied (storage.objects.delete missing)"
            )
        return super().put_json(key, document, overwrite=True)


class FailingJSONStore(InMemoryStore):
    """Fails the report JSON write, to prove the pointer never moves."""

    def put_json(self, key, document, overwrite=False):
        if key.endswith("report.json") and rs.DATA_ROOT in key:
            raise StorageError("simulated write failure")
        return super().put_json(key, document, overwrite=overwrite)


# --------------------------------------------------------------------------
# First write
# --------------------------------------------------------------------------

def test_a_first_report_writes_markdown_and_json(store):
    report, markdown = make_report()
    result = rs.publish(store, report, markdown, now=NOW)

    assert result.stored
    assert result.json_key == "reports/weekly/data/2026/08/2026-08-14/report.json"
    assert result.markdown_key == "reports/weekly/data/2026/08/2026-08-14/report.md"
    assert store.get_text(result.markdown_key) == markdown


def test_reports_live_under_a_prefix_that_can_expire_on_its_own(store):
    # latest/index must sit outside it: a GCS lifecycle rule can match a
    # prefix but cannot express an exclusion.
    report, markdown = make_report()
    result = rs.publish(store, report, markdown, now=NOW)

    assert result.json_key.startswith(rs.DATA_ROOT + "/")
    assert not rs.LATEST_KEY.startswith(rs.DATA_ROOT + "/")
    assert not rs.INDEX_KEY.startswith(rs.DATA_ROOT + "/")


def test_the_stored_document_round_trips_as_json(store):
    report, markdown = make_report()
    result = rs.publish(store, report, markdown, now=NOW)
    document = store.get_json(result.json_key)

    assert json.loads(json.dumps(document)) == document


# --------------------------------------------------------------------------
# Duplicate and revision safety
# --------------------------------------------------------------------------

def test_republishing_the_same_week_is_refused_by_default(store):
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)

    with pytest.raises(rs.DuplicateReport) as excinfo:
        rs.publish(store, report, markdown, now=NOW)
    assert "2026-08-14" in str(excinfo.value)


def test_the_revision_policy_files_a_rerun_without_touching_the_original(store):
    report, markdown = make_report()
    first = rs.publish(store, report, markdown, now=NOW)
    original = store.get_json(first.json_key)

    later = NOW + dt.timedelta(hours=3)
    revised = rs.publish(store, report, markdown, now=later,
                         on_duplicate=rs.ON_DUPLICATE_REVISION)

    assert revised.revision == "20260817T090000Z"
    assert "revisions/20260817T090000Z" in revised.json_key
    assert store.get_json(first.json_key) == original, "authoritative report changed"


def test_a_revision_records_its_own_keys_in_its_document(store):
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)
    revised = rs.publish(store, report, markdown, now=NOW + dt.timedelta(hours=1),
                         on_duplicate=rs.ON_DUPLICATE_REVISION)

    document = store.get_json(revised.json_key)
    assert document["storage"]["revision"] == revised.revision
    assert document["storage"]["json_key"] == revised.json_key


def test_the_index_counts_revisions_for_a_week(store):
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)
    rs.publish(store, report, markdown, now=NOW + dt.timedelta(hours=1),
               on_duplicate=rs.ON_DUPLICATE_REVISION)

    entry = rs.load_index(store)["entries"][0]
    assert entry["revisions"] == 1


def test_an_unknown_duplicate_policy_is_rejected(store):
    report, markdown = make_report()
    with pytest.raises(ValueError):
        rs.publish(store, report, markdown, now=NOW, on_duplicate="overwrite")


# --------------------------------------------------------------------------
# Latest pointer
# --------------------------------------------------------------------------

def test_the_pointer_identifies_everything_a_consumer_needs(store):
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)
    pointer = rs.load_latest(store)

    assert pointer["report_date"] == "2026-08-14"
    assert pointer["period"]["start"] == "2026-08-08"
    assert pointer["period"]["end"] == "2026-08-14"
    assert pointer["comparison_period"]["start"] == "2026-08-01"
    assert pointer["json_key"].endswith("report.json")
    assert pointer["markdown_key"].endswith("report.md")
    assert pointer["readiness"] == INSUFFICIENT_DATA
    assert pointer["generated_at"]
    assert pointer["pointer_updated_at"]
    assert pointer["schema_version"] == rs.SCHEMA_VERSION


def test_a_failed_report_write_does_not_update_latest():
    store = FailingJSONStore()
    report, markdown = make_report()

    with pytest.raises(StorageError):
        rs.publish(store, report, markdown, now=NOW)

    assert rs.load_latest(store) is None, "pointer moved to a report that was never stored"
    assert rs.load_index(store) is None


def test_publishing_an_older_week_does_not_drag_latest_backwards(store):
    newer, newer_md = make_report(today="2026-08-17")   # week ending 08-14
    older, older_md = make_report(today="2026-08-10")   # week ending 08-07
    rs.publish(store, newer, newer_md, now=NOW)

    result = rs.publish(store, older, older_md, now=NOW)

    assert result.stored
    assert rs.load_latest(store)["report_date"] == "2026-08-14"
    assert result.latest_unchanged_reason


def test_publishing_a_newer_week_does_move_latest(store):
    older, older_md = make_report(today="2026-08-10")
    newer, newer_md = make_report(today="2026-08-17")
    rs.publish(store, older, older_md, now=NOW)

    rs.publish(store, newer, newer_md, now=NOW)

    assert rs.load_latest(store)["report_date"] == "2026-08-14"


def test_latest_is_written_after_the_report_objects(store):
    order = []
    original = store.put_json

    def tracking_put(key, document, overwrite=False):
        order.append(key)
        return original(key, document, overwrite=overwrite)

    store.put_json = tracking_put
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)

    assert order.index(rs.LATEST_KEY) > order.index(
        "reports/weekly/data/2026/08/2026-08-14/report.json")


# --------------------------------------------------------------------------
# Staying inside the narrow delete grant
# --------------------------------------------------------------------------

def _record_overwrites(store):
    """Every key this store is asked to overwrite, in order."""
    overwritten = []
    put_json, put_text = store.put_json, store.put_text

    def json_spy(key, document, overwrite=False):
        if overwrite:
            overwritten.append(key)
        return put_json(key, document, overwrite=overwrite)

    def text_spy(key, text, overwrite=False, content_type="text/plain"):
        if overwrite:
            overwritten.append(key)
        return put_text(key, text, overwrite=overwrite, content_type=content_type)

    store.put_json, store.put_text = json_spy, text_spy
    return overwritten


def test_publishing_never_overwrites_anything_but_the_two_pointer_objects(store):
    """The bucket's IAM condition permits deleting exactly these two objects.

    If publish() ever tried to replace a dated report or a Clarity snapshot,
    GCS would refuse it — but the failure would surface as a broken weekly run
    rather than as the design error it is. Assert it here instead.
    """
    overwritten = _record_overwrites(store)

    for today in ("2026-08-10", "2026-08-17", "2026-08-24"):
        report, markdown = make_report(today=today)
        rs.publish(store, report, markdown, now=NOW)
    report, markdown = make_report(today="2026-08-17")
    rs.publish(store, report, markdown, now=NOW + dt.timedelta(hours=2),
               on_duplicate=rs.ON_DUPLICATE_REVISION)

    assert overwritten, "expected the pointer and index to be updated"
    assert set(overwritten) <= set(rs.MUTABLE_KEYS), (
        f"publish() overwrote {set(overwritten) - set(rs.MUTABLE_KEYS)}, which "
        "the narrow storage.objects.delete grant does not cover"
    )


def test_rebuilding_pointers_also_stays_inside_the_grant(store):
    for today in ("2026-08-10", "2026-08-17"):
        report, markdown = make_report(today=today)
        rs.publish(store, report, markdown, now=NOW)

    overwritten = _record_overwrites(store)
    rs.rebuild_pointers(store, now=NOW)

    assert set(overwritten) == set(rs.MUTABLE_KEYS)


def test_the_mutable_keys_are_exactly_the_two_documented_objects():
    assert rs.MUTABLE_KEYS == ("reports/weekly/latest.json",
                               "reports/weekly/index.json")
    # Neither may sit under the prefix a lifecycle rule would expire.
    assert not any(k.startswith(rs.DATA_ROOT + "/") for k in rs.MUTABLE_KEYS)


# --------------------------------------------------------------------------
# Degraded mode: the writer cannot overwrite
# --------------------------------------------------------------------------

def test_the_first_week_publishes_cleanly_even_with_a_create_only_writer():
    # Creating latest.json needs no delete permission — there is nothing to
    # replace yet. The gap only bites from the second week.
    store = DenyOverwriteStore()
    report, markdown = make_report(today="2026-08-10")

    result = rs.publish(store, report, markdown, now=NOW)

    assert result.stored and not result.degraded
    assert rs.load_latest(store)["report_date"] == "2026-08-07"


def test_the_second_week_stores_its_reports_but_cannot_move_the_pointer():
    store = DenyOverwriteStore()
    first, first_md = make_report(today="2026-08-10")
    rs.publish(store, first, first_md, now=NOW)

    second, second_md = make_report(today="2026-08-17")
    result = rs.publish(store, second, second_md, now=NOW)

    assert result.stored, "a permission gap must not cost the report itself"
    assert result.degraded
    assert not result.pointer_updated
    assert "storage.objects.delete" in result.pointer_error
    assert store.exists(result.json_key)
    # The pointer is stale, which is visibly old rather than quietly wrong.
    assert rs.load_latest(store)["report_date"] == "2026-08-07"


def test_the_degraded_publish_reports_exit_code_two(capsys):
    store = DenyOverwriteStore()
    first, first_md = make_report(today="2026-08-10")
    rs.publish(store, first, first_md, now=NOW)
    second, second_md = make_report(today="2026-08-17")

    code, result = wr.persist(store, second, second_md, NOW)

    assert code == 2, "a stale pointer is not the same failure as a lost report"
    assert result.stored


def test_pointers_can_be_rebuilt_from_the_stored_reports_alone(store):
    for today in ("2026-08-10", "2026-08-17"):
        report, markdown = make_report(today=today)
        rs.publish(store, report, markdown, now=NOW)

    # Simulate weeks published while the pointer writes were refused.
    del store._data[rs.LATEST_KEY]
    del store._data[rs.INDEX_KEY]

    index = rs.rebuild_pointers(store, now=NOW)

    assert [e["report_date"] for e in index["entries"]] == ["2026-08-14", "2026-08-07"]
    assert rs.load_latest(store)["report_date"] == "2026-08-14"


# --------------------------------------------------------------------------
# Historical index
# --------------------------------------------------------------------------

def test_the_index_starts_empty_and_grows_one_entry_per_week(store):
    assert rs.load_index(store) is None

    for today in ("2026-08-10", "2026-08-17"):
        report, markdown = make_report(today=today)
        rs.publish(store, report, markdown, now=NOW)

    index = rs.load_index(store)
    assert index["count"] == 2
    assert [e["report_date"] for e in index["entries"]] == ["2026-08-14", "2026-08-07"]


def test_an_index_entry_carries_the_numbers_that_outlive_the_report(store):
    report, markdown = make_report("healthy", today="2026-09-02")
    rs.publish(store, report, markdown, now=NOW)

    entry = rs.load_index(store)["entries"][0]
    assert entry["headline_metrics"]["ga4_sessions"] == 840
    assert entry["headline_metrics"]["gsc_clicks"]
    assert entry["readiness"] == READY
    assert entry["period_start"] and entry["period_end"]
    assert entry["json_key"] and entry["markdown_key"]


def test_the_index_stays_small(store):
    sizes = []
    for week in range(8):
        day = dt.date(2026, 8, 17) + dt.timedelta(days=7 * week)
        report, markdown = make_report(today=day.isoformat())
        rs.publish(store, report, markdown, now=NOW)
        sizes.append(len(json.dumps(rs.load_index(store))))

    assert rs.load_index(store)["count"] == 8
    # Marginal cost is what decides how the index ages. ~550 bytes a week
    # keeps a year around 29 KB — one fetch, no pagination.
    marginal = (sizes[-1] - sizes[0]) / (len(sizes) - 1)
    assert marginal < 700, f"{marginal:.0f} bytes per index entry is too fat"


def test_the_index_is_bounded_however_long_the_site_runs(monkeypatch, store):
    monkeypatch.setattr(rs, "INDEX_MAX_ENTRIES", 3)
    index = rs.empty_index(NOW)

    for week in range(6):
        day = dt.date(2026, 1, 7) + dt.timedelta(days=7 * week)
        rs.upsert_entry(index, {"report_date": day.isoformat()}, now=NOW)

    assert index["count"] == 3
    assert index["archived"]["count"] == 3
    assert index["archived"]["earliest_report_date"] == "2026-01-07"
    assert [e["report_date"] for e in index["entries"]] == [
        "2026-02-11", "2026-02-04", "2026-01-28"]


def test_republishing_a_week_replaces_its_index_line_rather_than_appending(store):
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)
    rs.publish(store, report, markdown, now=NOW + dt.timedelta(hours=1),
               on_duplicate=rs.ON_DUPLICATE_REVISION)

    index = rs.load_index(store)
    assert index["count"] == 1


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------

def test_a_consumer_reaches_the_newest_report_from_the_pointer_alone(store):
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)

    pointer = rs.load_latest(store)
    document = store.get_json(pointer["json_key"])

    assert document["report_date"] == pointer["report_date"]
    assert store.get_text(pointer["markdown_key"]) == markdown


def test_a_named_past_week_can_be_loaded_directly(store):
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)

    assert rs.load_report(store, "2026-08-14")["report_date"] == "2026-08-14"
    assert rs.load_report(store)["report_date"] == "2026-08-14"


def test_published_weeks_can_be_listed_without_the_index(store):
    for today in ("2026-08-10", "2026-08-17"):
        report, markdown = make_report(today=today)
        rs.publish(store, report, markdown, now=NOW)

    assert rs.published_dates(store) == ["2026-08-14", "2026-08-07"]


def test_loading_from_an_empty_store_says_so_rather_than_guessing(store):
    assert rs.load_latest(store) is None
    with pytest.raises(StorageError):
        rs.load_report(store)


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------

def test_the_document_declares_its_schema_version_and_kind(store):
    report, markdown = make_report()
    result = rs.publish(store, report, markdown, now=NOW)
    document = store.get_json(result.json_key)

    assert document["schema_version"] == rs.SCHEMA_VERSION
    assert document["kind"] == rs.REPORT_KIND
    assert rs.SCHEMA_VERSION.count(".") == 2


def test_the_schema_exposes_every_field_a_future_agent_was_promised(store):
    report, markdown = make_report("healthy", today="2026-09-02")
    result = rs.publish(store, report, markdown, now=NOW)
    document = store.get_json(result.json_key)

    for key in ("schema_version", "kind", "report_date", "period",
                "comparison_period", "facts", "inferences", "anomalies",
                "recommendations", "prioritized_actions", "readiness",
                "readiness_note", "findings", "conversions",
                "ecommerce_tracking_boundary", "data_quality",
                "source_coverage", "tracking_coverage", "headline_metrics",
                "storage"):
        assert key in document, key

    for view in ("ga4", "search_console", "clarity", "seo",
                 "landing_pages_and_cro", "ux", "cross_source"):
        assert view in document["findings"], view


def test_named_views_reference_facts_rather_than_copying_them(store):
    # Sections hold ids so a finding exists once and two copies cannot drift.
    report, markdown = make_report("healthy", today="2026-09-02")
    result = rs.publish(store, report, markdown, now=NOW)
    document = store.get_json(result.json_key)

    known = {f["id"] for f in document["facts"]}
    assert document["findings"]["ga4"]
    assert set(document["findings"]["ga4"]).issubset(known)


def test_the_conversion_state_and_boundary_survive_into_storage(store):
    report, markdown = make_report(today="2026-08-17")
    result = rs.publish(store, report, markdown, now=NOW)
    document = store.get_json(result.json_key)

    assert document["conversions"]["state"] == "before_ecommerce_tracking"
    assert "not an absence of sales" in document["conversions"]["message"]
    assert document["ecommerce_tracking_boundary"]["period_state"]


def test_headline_metrics_are_site_level_only(store):
    report, _ = make_report("healthy", today="2026-09-02")
    metrics = rs.headline_metrics(report)

    assert metrics["ga4_sessions"] == 840
    assert set(metrics).issubset(set(rs.HEADLINE_METRICS))


# --------------------------------------------------------------------------
# Retention design
# --------------------------------------------------------------------------

def test_every_document_declares_that_no_lifecycle_policy_is_applied_yet(store):
    report, markdown = make_report()
    result = rs.publish(store, report, markdown, now=NOW)
    retention = store.get_json(result.json_key)["storage"]["retention"]

    assert retention["policy_applied"] is False
    assert retention["recommended_days"] == rs.RETENTION_DAYS
    assert retention["expiring_prefix"] == "reports/weekly/data/"
    assert rs.LATEST_KEY in retention["permanent_keys"]
    assert rs.INDEX_KEY in retention["permanent_keys"]


def test_the_recommended_retention_outlives_a_year_so_yoy_stays_possible():
    # 365 would delete the comparison week days before it is needed.
    assert rs.RETENTION_DAYS > 365
    assert "NOT YET APPLIED" in rs.RETENTION_NOTE


def test_the_index_declares_the_same_retention_intent(store):
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)

    assert rs.load_index(store)["retention"]["policy_applied"] is False


# --------------------------------------------------------------------------
# Guardrails carried forward from earlier phases
# --------------------------------------------------------------------------

def test_low_volume_recommendation_gating_survives_storage(store):
    report, markdown = make_report("low_volume")
    result = rs.publish(store, report, markdown, now=NOW)
    document = store.get_json(result.json_key)

    assert document["readiness"] == INSUFFICIENT_DATA
    assert all(r["priority"] == PRIORITY_MONITOR
               for r in document["recommendations"])
    assert "insufficient data for recommendation" in document["readiness_note"]


def test_storing_a_report_makes_no_clarity_api_call(store):
    # The autouse fixture turns any Clarity call into a failure; completing
    # the publish is the proof.
    report, markdown = make_report()
    assert rs.publish(store, report, markdown, now=NOW).stored


def test_persisting_a_fixture_run_into_real_history_is_refused(tmp_path):
    code = wr.main(["--fixture", "low_volume", "--out-dir", str(tmp_path), "--persist"])
    assert code == 1


def test_reports_are_not_written_into_the_repository(tmp_path, store):
    before = set(Path(".").glob("**/*.md"))
    report, markdown = make_report()
    rs.publish(store, report, markdown, now=NOW)
    assert set(Path(".").glob("**/*.md")) == before
    assert rs.ROOT not in {str(p) for p in Path(".").iterdir()}
