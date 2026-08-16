#!/usr/bin/env python3
"""
Google Cloud Storage backend — the durable production store.

Implements the same SnapshotStore interface as LocalFileStore, so switching is
a constructor change and nothing else moves.

WHY THE PRECONDITION MATTERS

Clarity's history cannot be backfilled: a day overwritten is a day gone. Every
create therefore goes out with `if_generation_match=0`, which is GCS's atomic
create-if-absent — the write fails server-side if the object already exists,
even under a race between two collectors. Overwriting is possible, but only
when a caller passes overwrite=True explicitly, and never for a raw snapshot
(those are keyed by collection instant, so a re-collection is a new object).

CREDENTIALS

A separate identity from the read-only GA4/Search Console service account. The
reader must stay read-only; the writer needs object access to one bucket and
nothing else. The key is read from ANALYTICS_STORAGE_SA_JSON (raw or base64),
parsed in memory, registered with the redactor, and never logged. Application
Default Credentials are used when the variable is absent, so Workload Identity
works without code changes.

The google-cloud-storage import is deferred to construction time, so this
module imports cleanly — and the offline tests run — without the dependency
installed.
"""

import base64
import binascii
import json
import os

from analytics_common import redact, register_secret
from storage import PermissionDeniedError, SnapshotStore, StorageError

CREDENTIAL_ENV = "ANALYTICS_STORAGE_SA_JSON"
BUCKET_ENV = "ANALYTICS_BUCKET"

# Only what this backend needs. Anything wider is a permissions smell.
REQUIRED_PERMISSIONS = (
    "storage.objects.create",
    "storage.objects.get",
    "storage.objects.list",
)


def load_storage_credentials_info(env_var=CREDENTIAL_ENV):
    """Parse the writer service account key from the environment.

    Returns None when unset, so the caller falls back to Application Default
    Credentials. Errors never quote the payload.
    """
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        return None

    text = raw
    if not text.startswith("{"):
        try:
            text = base64.b64decode(text, validate=True).decode("utf-8").strip()
        except (binascii.Error, ValueError, UnicodeDecodeError):
            pass

    try:
        info = json.loads(text)
    except json.JSONDecodeError as exc:
        raise StorageError(
            f"Could not parse {env_var} as JSON (error at line {exc.lineno}, "
            f"column {exc.colno}). Expected a service account key, raw or base64."
        ) from None

    if not isinstance(info, dict) or not info.get("private_key"):
        raise StorageError(
            f"{env_var} does not look like a service account key "
            "(no private_key field)."
        )

    # Any later error text quoting the key is scrubbed from here on.
    register_secret(info["private_key"])
    if info.get("private_key_id"):
        register_secret(info["private_key_id"])
    return info


def _build_client(credentials_info=None, project=None):
    try:
        from google.cloud import storage as gcs
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise StorageError(
            "google-cloud-storage is not installed. Install it from "
            "automations/analytics/requirements.txt to use the GCS backend."
        ) from exc

    if credentials_info:
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        return gcs.Client(project=project or credentials_info.get("project_id"),
                          credentials=credentials)
    return gcs.Client(project=project)


class GCSStore(SnapshotStore):
    """Durable snapshot store backed by one Cloud Storage bucket.

    Keys map directly to object names under an optional prefix, so the layout
    on disk and the layout in the bucket are identical and a local store can be
    copied up without translation.
    """

    durable = True

    def __init__(self, bucket_name, prefix="", client=None, credentials_info=None,
                 project=None):
        if not bucket_name:
            raise StorageError(
                f"No bucket configured. Pass bucket_name or set {BUCKET_ENV}."
            )
        self.bucket_name = bucket_name
        self.prefix = prefix.strip("/")
        self._client = client or _build_client(
            credentials_info if credentials_info is not None
            else load_storage_credentials_info(),
            project=project,
        )
        self._bucket = self._client.bucket(bucket_name)

    # -- key mapping -------------------------------------------------------

    def _object_name(self, key):
        if key.startswith("/") or ".." in key.split("/"):
            raise StorageError(f"unsafe key: {key!r}")
        return f"{self.prefix}/{key}" if self.prefix else key

    def _key(self, object_name):
        if self.prefix and object_name.startswith(self.prefix + "/"):
            return object_name[len(self.prefix) + 1:]
        return object_name

    # -- SnapshotStore -----------------------------------------------------

    def _upload(self, key, body, content_type, overwrite):
        blob = self._bucket.blob(self._object_name(key))
        try:
            if overwrite:
                blob.upload_from_string(body, content_type=content_type)
            else:
                # Atomic create-if-absent. Fails server-side if the object
                # exists, so two collectors racing cannot clobber a snapshot.
                blob.upload_from_string(
                    body, content_type=content_type, if_generation_match=0,
                )
        except Exception as exc:  # noqa: BLE001 — re-raised as StorageError
            if _is_precondition_failure(exc):
                raise StorageError(
                    f"key already exists: {key}. Historical snapshots are never "
                    "overwritten silently; pass overwrite=True only for derived data."
                ) from None
            if overwrite and _is_permission_denied(exc):
                # GCS models "replace an object" as delete-then-create, so a
                # writer scoped to create/get/list cannot overwrite. Say so
                # precisely — the generic message would send someone hunting
                # for a bucket or network problem that does not exist.
                raise PermissionDeniedError(
                    f"overwrite of {key} was denied. Replacing an object in GCS "
                    "requires storage.objects.delete in addition to "
                    "storage.objects.create; the analytics writer currently has "
                    "create/get/list only."
                ) from None
            raise StorageError(f"GCS write failed for {key}: {redact(exc)}") from None

    def put_json(self, key, document, overwrite=False):
        body = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        self._upload(key, body, "application/json", overwrite)

    def put_text(self, key, text, overwrite=False, content_type="text/plain"):
        self._upload(key, str(text), f"{content_type}; charset=utf-8", overwrite)

    def get_text(self, key):
        blob = self._bucket.blob(self._object_name(key))
        try:
            return blob.download_as_text()
        except Exception as exc:  # noqa: BLE001
            if _is_not_found(exc):
                raise StorageError(f"no such key: {key}") from None
            raise StorageError(f"GCS read failed for {key}: {redact(exc)}") from None

    def get_json(self, key):
        body = self.get_text(key)
        try:
            return json.loads(body)
        except ValueError as exc:
            raise StorageError(f"stored object is not valid JSON: {key} ({exc})") from None

    def list_keys(self, prefix=""):
        full_prefix = self._object_name(prefix) if prefix else (self.prefix or "")
        try:
            blobs = self._client.list_blobs(self.bucket_name, prefix=full_prefix or None)
            return sorted(self._key(b.name) for b in blobs)
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"GCS list failed for {prefix!r}: {redact(exc)}") from None

    def exists(self, key):
        try:
            return bool(self._bucket.blob(self._object_name(key)).exists())
        except Exception as exc:  # noqa: BLE001
            raise StorageError(f"GCS exists check failed for {key}: {redact(exc)}") from None

    def describe(self):
        location = f"gs://{self.bucket_name}" + (f"/{self.prefix}" if self.prefix else "")
        return f"GCSStore({location}, durable=True)"


def _is_precondition_failure(exc):
    if getattr(exc, "code", None) == 412:
        return True
    name = type(exc).__name__
    return "PreconditionFailed" in name or "412" in str(exc)


def _is_permission_denied(exc):
    if getattr(exc, "code", None) in (401, 403):
        return True
    name = type(exc).__name__
    return "Forbidden" in name or "403" in str(exc)


def _is_not_found(exc):
    if getattr(exc, "code", None) == 404:
        return True
    name = type(exc).__name__
    return "NotFound" in name or "404" in str(exc)


def store_from_env(bucket_name=None, prefix=""):
    """Build the production store from environment configuration.

    Used by the collector once the bucket exists; raises a clear error rather
    than silently falling back to a non-durable local store, because a silent
    fallback would look like success and preserve nothing.
    """
    bucket = bucket_name or os.environ.get(BUCKET_ENV, "").strip()
    if not bucket:
        raise StorageError(
            f"{BUCKET_ENV} is not set. Refusing to fall back to a non-durable "
            "local store: Clarity history cannot be backfilled, so a silent "
            "fallback would look like success and preserve nothing."
        )
    return GCSStore(bucket, prefix=prefix or os.environ.get("ANALYTICS_PREFIX", ""))
