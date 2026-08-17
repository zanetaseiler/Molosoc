#!/usr/bin/env python3
"""
The one place a client-specific identifier is resolved.

The interpretation layer and its handoff document are meant to be reusable
across clients, so nothing below them should carry a brand name in a constant.
This resolves the slug once, from the environment, with a committed default —
the same pattern `ECOMMERCE_TRACKING_START` already uses, and for the same
reason: an unset variable must not silently produce a differently-named
document, because a consumer keying on `kind` would stop recognising it.

MOLOSOC stays the configured value for this project. It is the default rather
than a hardcoded string, which is the whole difference.

Deliberately NOT parameterised here: `report_store.REPORT_KIND`. Weekly
reports carrying that kind are already stored in the bucket, and changing how
it is derived risks a mismatch against history that exists. Reusing this
module for a second client means setting CLIENT_SLUG in that client's own
repository, where no such history exists.
"""

import os
import re

CLIENT_SLUG_ENV = "CLIENT_SLUG"

#: The configured value for this project. A variable overrides it.
DEFAULT_CLIENT_SLUG = "molosoc"

#: Lowercase, digits, underscore. A slug becomes part of a document `kind`
#: that consumers match on, so a stray space or capital is a silent mismatch
#: rather than an error at the point it is introduced.
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")


class ConfigError(ValueError):
    pass


def client_slug(env=None):
    env = os.environ if env is None else env
    slug = (env.get(CLIENT_SLUG_ENV) or "").strip() or DEFAULT_CLIENT_SLUG
    if not _SLUG_RE.match(slug):
        raise ConfigError(
            f"{CLIENT_SLUG_ENV}={slug!r} is not a valid slug. Use lowercase "
            "letters, digits and underscores, starting with a letter or digit.")
    return slug


def namespaced(suffix, slug=None, env=None):
    """`<slug>.<suffix>` — the naming scheme every document kind follows."""
    return f"{slug or client_slug(env)}.{suffix}"
