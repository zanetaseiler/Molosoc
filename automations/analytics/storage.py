#!/usr/bin/env python3
"""
Durable storage for analytics snapshots, behind one interface.

Clarity's Live Insights endpoint returns at most three days of data. Anything
older exists only if this system stored it, and no later engineering can
backfill it — so where snapshots land is a decision with permanent
consequences, not an implementation detail.

That decision is not made here. This module defines the interface and ships
two backends that need no infrastructure:

* LocalFileStore  — JSONL on disk. Correct for development, tests, and running
                    the collector from a workstation.
* InMemoryStore   — tests only.

A production backend (object storage) implements the same three methods and is
dropped in without touching any caller. See README for the recommendation and
the decision it needs.

LocalFileStore is deliberately not safe to use from an ephemeral CI runner:
the filesystem is discarded when the job ends, so a "successful" collection
would silently store nothing. is_durable() reports this, and callers that
matter check it rather than assuming.
"""

import json
import os
import tempfile
from abc import ABC, abstractmethod


class StorageError(RuntimeError):
    pass


class SnapshotStore(ABC):
    """Append-oriented key/value store for JSON documents and record streams.

    Keys are POSIX-style paths, e.g. "raw/clarity/2026-08-14/…json". Backends
    map them onto directories, object keys, or table rows as they see fit.
    """

    #: False for backends whose contents do not survive the process/host.
    durable = False

    @abstractmethod
    def put_json(self, key, document, overwrite=False):
        """Write one JSON document. Raises unless overwrite when key exists."""

    @abstractmethod
    def get_json(self, key):
        """Read one JSON document. Raises StorageError if absent."""

    @abstractmethod
    def list_keys(self, prefix=""):
        """Every key under prefix, sorted."""

    def exists(self, key):
        return key in set(self.list_keys())

    # -- record streams (JSONL) --------------------------------------------

    def put_records(self, key, records, overwrite=False):
        """Store MetricRecords as a JSONL document."""
        payload = {"records": [r.to_dict() for r in records]}
        self.put_json(key, payload, overwrite=overwrite)

    def get_records(self, key):
        from records import MetricRecord

        document = self.get_json(key)
        return [MetricRecord.from_dict(row) for row in document.get("records", [])]

    def is_durable(self):
        return self.durable

    def describe(self):
        return f"{type(self).__name__}(durable={self.durable})"


class InMemoryStore(SnapshotStore):
    """Test backend. Never durable, by definition."""

    durable = False

    def __init__(self):
        self._data = {}

    def put_json(self, key, document, overwrite=False):
        if key in self._data and not overwrite:
            raise StorageError(f"key already exists: {key}")
        # Round-trip so callers cannot mutate stored state by reference.
        self._data[key] = json.loads(json.dumps(document))

    def get_json(self, key):
        if key not in self._data:
            raise StorageError(f"no such key: {key}")
        return json.loads(json.dumps(self._data[key]))

    def list_keys(self, prefix=""):
        return sorted(k for k in self._data if k.startswith(prefix))

    def exists(self, key):
        return key in self._data


class LocalFileStore(SnapshotStore):
    """JSON documents under a root directory.

    Writes are atomic (temp file plus rename) so an interrupted run cannot
    leave a half-written snapshot that later parses as valid-but-truncated.
    """

    durable = False  # survives the process, not the CI runner — see module docstring

    def __init__(self, root):
        self.root = os.path.abspath(root)

    def _path(self, key):
        if key.startswith("/") or ".." in key.split("/"):
            raise StorageError(f"unsafe key: {key!r}")
        return os.path.join(self.root, *key.split("/"))

    def put_json(self, key, document, overwrite=False):
        path = self._path(key)
        if os.path.exists(path) and not overwrite:
            raise StorageError(f"key already exists: {key}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=os.path.dirname(path), delete=False, suffix=".tmp",
        )
        try:
            with handle:
                json.dump(document, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(handle.name, path)
        except Exception:
            if os.path.exists(handle.name):
                os.unlink(handle.name)
            raise

    def get_json(self, key):
        path = self._path(key)
        if not os.path.isfile(path):
            raise StorageError(f"no such key: {key}")
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def list_keys(self, prefix=""):
        found = []
        for dirpath, _dirnames, filenames in os.walk(self.root):
            for name in filenames:
                full = os.path.join(dirpath, name)
                key = os.path.relpath(full, self.root).replace(os.sep, "/")
                if key.startswith(prefix):
                    found.append(key)
        return sorted(found)

    def exists(self, key):
        return os.path.isfile(self._path(key))

    def describe(self):
        return f"LocalFileStore(root={self.root}, durable={self.durable})"


# --- key layout ------------------------------------------------------------
# One place that knows how snapshots are addressed, so a backend swap or a
# layout change is a single edit.

def raw_key(source, date, collected_at):
    """Raw API payload. Keyed by collection instant as well as date, so a
    re-collection is a new revision and never overwrites the original."""
    stamp = str(collected_at).replace(":", "").replace("-", "").replace("+", "Z")
    return f"raw/{source}/{date}/{stamp}.json"


def facts_key(source, date):
    """Normalized records. Derived, so rewriting is expected and safe."""
    return f"facts/{source}/{date}.json"


def state_key(name, date):
    return f"state/{name}/{date}.json"


def raw_prefix(source, date=None):
    return f"raw/{source}/" + (f"{date}/" if date else "")
