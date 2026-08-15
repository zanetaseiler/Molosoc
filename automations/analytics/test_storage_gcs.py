#!/usr/bin/env python3
"""
Offline tests for the GCS backend.

The Cloud Storage client is emulated, including generation preconditions and
NotFound behaviour, so the whole suite runs with no network, no credentials and
no bucket. Live GCS is never required.

The precondition behaviour is the important part: Clarity history cannot be
backfilled, so a create that silently overwrites an existing snapshot would
destroy data permanently.

Run with:  python3 -m pytest automations/analytics/
"""

import base64
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import analytics_common  # noqa: E402
import storage_gcs as sg  # noqa: E402
from records import CLARITY, MetricRecord, PERFORMANCE, SITE, SITE_ENTITY_ID  # noqa: E402
from storage import StorageError, facts_key, raw_key  # noqa: E402

BUCKET = "molosoc-analytics-history"

FAKE_KEY = {
    "type": "service_account",
    "project_id": "molosoc-analytics",
    "private_key_id": "storagekeyid123",
    "private_key": "-----BEGIN PRIVATE KEY-----\nSTORAGEFAKEKEYMATERIAL\n-----END PRIVATE KEY-----\n",
    "client_email": "molosoc-analytics-writer@molosoc-analytics.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
}


# --------------------------------------------------------------------------
# Emulated Cloud Storage client
# --------------------------------------------------------------------------

class NotFound(Exception):
    code = 404


class PreconditionFailed(Exception):
    code = 412


class FakeBlob:
    def __init__(self, bucket, name):
        self._bucket = bucket
        self.name = name

    def upload_from_string(self, body, content_type=None, if_generation_match=None):
        if if_generation_match == 0 and self.name in self._bucket.objects:
            raise PreconditionFailed("object already exists")
        self._bucket.objects[self.name] = body
        self._bucket.writes.append((self.name, if_generation_match))

    def download_as_text(self):
        if self.name not in self._bucket.objects:
            raise NotFound(f"no such object: {self.name}")
        return self._bucket.objects[self.name]

    def exists(self):
        return self.name in self._bucket.objects


class FakeBucket:
    def __init__(self, name):
        self.name = name
        self.objects = {}
        self.writes = []

    def blob(self, name):
        return FakeBlob(self, name)


class FakeClient:
    def __init__(self):
        self.buckets = {}

    def bucket(self, name):
        return self.buckets.setdefault(name, FakeBucket(name))

    def list_blobs(self, bucket_name, prefix=None):
        bucket = self.buckets.setdefault(bucket_name, FakeBucket(bucket_name))
        return [FakeBlob(bucket, name) for name in sorted(bucket.objects)
                if not prefix or name.startswith(prefix)]


@pytest.fixture(autouse=True)
def isolate_secrets(monkeypatch):
    monkeypatch.delenv(sg.CREDENTIAL_ENV, raising=False)
    monkeypatch.delenv(sg.BUCKET_ENV, raising=False)
    analytics_common.reset_secrets()
    yield
    analytics_common.reset_secrets()


@pytest.fixture
def client():
    return FakeClient()


@pytest.fixture
def store(client):
    return sg.GCSStore(BUCKET, client=client)


# --------------------------------------------------------------------------
# Interface conformance
# --------------------------------------------------------------------------

def test_json_documents_round_trip(store):
    store.put_json("facts/clarity/2026-08-14.json", {"records": [{"metric": "clarity_sessions"}]})
    assert store.get_json("facts/clarity/2026-08-14.json")["records"][0]["metric"] == "clarity_sessions"


def test_missing_key_raises_the_same_error_as_the_local_store(store):
    with pytest.raises(StorageError, match="no such key"):
        store.get_json("nope.json")


def test_exists(store):
    assert store.exists("a.json") is False
    store.put_json("a.json", {})
    assert store.exists("a.json") is True


def test_list_keys_filters_by_prefix(store):
    store.put_json("raw/clarity/2026-08-13/a.json", {})
    store.put_json("raw/clarity/2026-08-14/b.json", {})
    store.put_json("facts/clarity/2026-08-14.json", {})

    assert len(store.list_keys("raw/clarity/")) == 2
    assert store.list_keys("facts/") == ["facts/clarity/2026-08-14.json"]


def test_records_round_trip_through_the_bucket(store):
    rows = [MetricRecord(date="2026-08-14", source=CLARITY, entity_type=SITE,
                         entity_id=SITE_ENTITY_ID, metric="clarity_sessions",
                         value=85, metric_class=PERFORMANCE)]
    store.put_records(facts_key(CLARITY, "2026-08-14"), rows)
    assert store.get_records(facts_key(CLARITY, "2026-08-14")) == rows


def test_stored_body_is_machine_readable_json(store, client):
    store.put_json("a.json", {"b": 1})
    raw = client.buckets[BUCKET].objects["a.json"]
    assert json.loads(raw) == {"b": 1}


def test_corrupt_object_is_reported_not_silently_empty(store, client):
    client.buckets[BUCKET].objects["a.json"] = "not json{"
    with pytest.raises(StorageError, match="not valid JSON"):
        store.get_json("a.json")


# --------------------------------------------------------------------------
# Never silently overwrite an authoritative snapshot
# --------------------------------------------------------------------------

def test_creates_use_an_if_generation_match_precondition(store, client):
    store.put_json("raw/clarity/2026-08-14/x.json", {"payload": []})
    name, precondition = client.buckets[BUCKET].writes[0]
    # 0 means "only if the object does not exist" — atomic, server-side.
    assert precondition == 0


def test_a_second_create_for_the_same_key_is_refused(store):
    store.put_json("raw/clarity/2026-08-14/x.json", {"payload": ["first"]})
    with pytest.raises(StorageError, match="already exists"):
        store.put_json("raw/clarity/2026-08-14/x.json", {"payload": ["second"]})


def test_a_refused_write_leaves_the_original_intact(store):
    store.put_json("a.json", {"v": "original"})
    with pytest.raises(StorageError):
        store.put_json("a.json", {"v": "clobbered"})
    assert store.get_json("a.json") == {"v": "original"}


def test_overwrite_is_possible_but_must_be_explicit(store, client):
    store.put_json("facts/clarity/2026-08-14.json", {"v": 1})
    store.put_json("facts/clarity/2026-08-14.json", {"v": 2}, overwrite=True)

    assert store.get_json("facts/clarity/2026-08-14.json") == {"v": 2}
    assert client.buckets[BUCKET].writes[-1][1] is None  # no precondition


def test_raw_snapshot_keys_never_collide_across_collections(store):
    # Re-collection is a new object, so the precondition never even fires.
    first = raw_key(CLARITY, "2026-08-14", "2026-08-14T06:00:00+00:00")
    second = raw_key(CLARITY, "2026-08-14", "2026-08-14T18:00:00+00:00")
    store.put_json(first, {"payload": ["morning"]})
    store.put_json(second, {"payload": ["evening"]})

    assert store.get_json(first)["payload"] == ["morning"]
    assert len(store.list_keys("raw/clarity/2026-08-14/")) == 2


def test_precondition_errors_are_recognized_by_code_and_by_name():
    assert sg._is_precondition_failure(PreconditionFailed("boom"))
    assert sg._is_precondition_failure(RuntimeError("412 Precondition Failed"))
    assert not sg._is_precondition_failure(RuntimeError("500 oops"))


def test_not_found_errors_are_recognized_by_code_and_by_name():
    assert sg._is_not_found(NotFound("gone"))
    assert sg._is_not_found(RuntimeError("404 Not Found"))
    assert not sg._is_not_found(RuntimeError("500 oops"))


# --------------------------------------------------------------------------
# Durability and layout
# --------------------------------------------------------------------------

def test_the_gcs_store_reports_itself_as_durable(store):
    assert store.is_durable() is True
    assert "gs://molosoc-analytics-history" in store.describe()


def test_date_partitioned_layout_is_preserved_in_the_bucket(store, client):
    store.put_json(raw_key(CLARITY, "2026-08-14", "2026-08-14T06:00:00+00:00"), {})
    store.put_json(facts_key(CLARITY, "2026-08-14"), {})

    names = sorted(client.buckets[BUCKET].objects)
    assert names[0].startswith("facts/clarity/2026-08-14")
    assert names[1].startswith("raw/clarity/2026-08-14/")


def test_an_optional_prefix_namespaces_the_bucket(client):
    store = sg.GCSStore(BUCKET, prefix="molosoc", client=client)
    store.put_json("facts/clarity/2026-08-14.json", {})

    assert "molosoc/facts/clarity/2026-08-14.json" in client.buckets[BUCKET].objects
    # Keys stay prefix-free for callers, so a prefix change moves nothing else.
    assert store.list_keys("facts/") == ["facts/clarity/2026-08-14.json"]
    assert store.get_json("facts/clarity/2026-08-14.json") == {}


def test_unsafe_keys_are_rejected(store):
    with pytest.raises(StorageError, match="unsafe key"):
        store.put_json("../escape.json", {})
    with pytest.raises(StorageError, match="unsafe key"):
        store.put_json("/absolute.json", {})


def test_a_missing_bucket_name_is_refused(client):
    with pytest.raises(StorageError, match="No bucket configured"):
        sg.GCSStore("", client=client)


# --------------------------------------------------------------------------
# Credentials
# --------------------------------------------------------------------------

def test_no_credential_env_falls_back_to_application_default():
    # Returning None lets Workload Identity work without code changes.
    assert sg.load_storage_credentials_info() is None


def test_raw_json_credentials_are_parsed(monkeypatch):
    monkeypatch.setenv(sg.CREDENTIAL_ENV, json.dumps(FAKE_KEY))
    info = sg.load_storage_credentials_info()
    assert info["client_email"] == FAKE_KEY["client_email"]


def test_base64_credentials_are_parsed(monkeypatch):
    encoded = base64.b64encode(json.dumps(FAKE_KEY).encode()).decode()
    monkeypatch.setenv(sg.CREDENTIAL_ENV, encoded)
    assert sg.load_storage_credentials_info()["project_id"] == "molosoc-analytics"


def test_loading_credentials_registers_the_key_for_redaction(monkeypatch):
    monkeypatch.setenv(sg.CREDENTIAL_ENV, json.dumps(FAKE_KEY))
    sg.load_storage_credentials_info()

    scrubbed = analytics_common.redact(f"failed: {FAKE_KEY['private_key']}")
    assert "STORAGEFAKEKEYMATERIAL" not in scrubbed
    assert "storagekeyid123" not in analytics_common.redact("id storagekeyid123 leaked")


def test_malformed_credentials_error_never_quotes_the_payload(monkeypatch):
    monkeypatch.setenv(sg.CREDENTIAL_ENV, json.dumps(FAKE_KEY)[:130])
    with pytest.raises(StorageError) as exc:
        sg.load_storage_credentials_info()

    message = str(exc.value)
    assert "STORAGEFAKEKEYMATERIAL" not in message
    assert "PRIVATE KEY" not in message
    assert "line" in message


def test_a_non_service_account_credential_is_rejected(monkeypatch):
    monkeypatch.setenv(sg.CREDENTIAL_ENV, json.dumps({"type": "authorized_user"}))
    with pytest.raises(StorageError, match="private_key"):
        sg.load_storage_credentials_info()


def test_gcs_errors_are_redacted_before_being_raised(monkeypatch, client):
    monkeypatch.setenv(sg.CREDENTIAL_ENV, json.dumps(FAKE_KEY))
    sg.load_storage_credentials_info()
    store = sg.GCSStore(BUCKET, client=client)

    def leaky_upload(*_a, **_kw):
        raise RuntimeError(f"upload rejected for key {FAKE_KEY['private_key']}")

    monkeypatch.setattr(FakeBlob, "upload_from_string", leaky_upload)
    with pytest.raises(StorageError) as exc:
        store.put_json("a.json", {})

    assert "STORAGEFAKEKEYMATERIAL" not in str(exc.value)
    assert "[REDACTED]" in str(exc.value)


def test_minimum_permissions_are_documented_and_narrow():
    # If this list grows, the IAM role handed to the writer must be re-justified.
    assert set(sg.REQUIRED_PERMISSIONS) == {
        "storage.objects.create", "storage.objects.get", "storage.objects.list",
    }
    assert not any("delete" in p for p in sg.REQUIRED_PERMISSIONS)
    assert not any("admin" in p.lower() for p in sg.REQUIRED_PERMISSIONS)


# --------------------------------------------------------------------------
# Environment wiring
# --------------------------------------------------------------------------

def test_store_from_env_refuses_to_fall_back_to_a_local_store():
    # A silent fallback would report success and preserve nothing.
    with pytest.raises(StorageError, match="Refusing to fall back"):
        sg.store_from_env()
