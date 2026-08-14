#!/usr/bin/env python3
"""
URL canonicalization and host classification.

Every source names pages differently. GA4 reports a path
(`/product/molosoc-hydratacni-navleky-na-nohy/`), Search Console reports an
absolute URL (`https://molosoc.com/product/...`), Clarity reports whatever the
browser saw. Without one canonical identity, cross-source page analysis joins
nothing.

The verification runs made this concrete: GA4's landing-page report already
splits the homepage across `/`, `/?fbclid=IwcGRvZ...` and a second `fbclid`
variant — three rows that are one page. Search Console separately returned
`staging.molosoc.com` URLs, which are not part of the marketing site at all.

Two decisions worth knowing about:

* Tracking parameters are removed by **denylist**, not allowlist. An unknown
  parameter is kept, because dropping one that genuinely identifies content
  (`?lang=cs` under Polylang, a WooCommerce variation, an on-site search term)
  silently merges two different pages into one. Over-keeping splits a page in
  two and is visible; over-dropping fuses two pages and is not.
* Host classification is separate from canonicalization. A staging URL still
  canonicalizes correctly — it is simply labelled non-production so the
  analytics layer can exclude it explicitly and count what it excluded.
"""

from collections import Counter
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

DEFAULT_ORIGIN = "https://molosoc.com"

# Exact-match tracking parameters. Ad-platform click ids and analytics
# stitching parameters — none of them ever identify different content.
TRACKING_PARAMS = frozenset({
    # Google
    "gclid", "gclsrc", "gbraid", "wbraid", "dclid", "gad_source", "gad_campaignid",
    "srsltid",
    # Meta
    "fbclid", "fb_action_ids", "fb_action_types", "fb_source",
    # Microsoft / Bing
    "msclkid",
    # Other ad networks and social
    "ttclid", "twclid", "li_fat_id", "igshid", "igsh", "yclid", "epik", "s_kwcid",
    "vero_id", "vero_conv", "sc_cid", "mkt_tok", "wickedid", "rb_clickid",
    # Email / CRM
    "mc_cid", "mc_eid", "_hsenc", "_hsmi", "oly_enc_id", "oly_anon_id",
    # Google Analytics cross-domain stitching
    "_ga", "_gl", "gaid",
})

# Prefix rules for parameter families that grow over time.
TRACKING_PREFIXES = ("utm_", "pk_", "mtm_", "piwik_", "matomo_", "hsa_")

# Hosts serving the live marketing site. Both spellings of the apex resolve to
# one canonical host.
PRODUCTION_HOSTS = frozenset({"molosoc.com", "www.molosoc.com"})

# Known non-production hosts, plus subdomain prefixes that indicate one.
NON_PRODUCTION_HOSTS = frozenset({"staging.molosoc.com"})
NON_PRODUCTION_PREFIXES = ("staging.", "stage.", "dev.", "test.", "preview.", "uat.", "sandbox.")
NON_PRODUCTION_SUFFIXES = (".local", ".test", ".localhost", ".invalid")

PRODUCTION = "production"
NON_PRODUCTION = "non_production"
UNKNOWN = "unknown"

# GA4 emits these for rows it cannot attribute. They are real rows with real
# sessions, so they are kept as an explicit entity rather than dropped.
UNATTRIBUTED = "(unattributed)"
GA4_NULL_VALUES = frozenset({"", "(not set)", "(none)", "(other)"})


class CanonicalUrl:
    """The canonical identity of a page, plus what was done to get there."""

    __slots__ = ("url", "host", "path", "query", "classification", "dropped_params", "original")

    def __init__(self, url, host, path, query, classification, dropped_params, original):
        self.url = url
        self.host = host
        self.path = path
        self.query = query
        self.classification = classification
        self.dropped_params = dropped_params
        self.original = original

    @property
    def is_production(self):
        return self.classification == PRODUCTION

    @property
    def is_unattributed(self):
        return self.url == UNATTRIBUTED

    def __str__(self):
        return self.url

    def __eq__(self, other):
        if isinstance(other, CanonicalUrl):
            return self.url == other.url
        return NotImplemented

    def __hash__(self):
        return hash(self.url)

    def __repr__(self):
        return f"CanonicalUrl({self.url!r}, {self.classification})"


def is_tracking_param(name):
    lowered = name.lower()
    return lowered in TRACKING_PARAMS or lowered.startswith(TRACKING_PREFIXES)


def classify_host(host):
    """production / non_production / unknown.

    Unknown is a distinct outcome, not a synonym for non-production: a host we
    have never seen should surface for a human decision rather than being
    quietly kept or quietly dropped.
    """
    host = (host or "").lower().strip()
    if not host:
        return UNKNOWN
    if host in NON_PRODUCTION_HOSTS:
        return NON_PRODUCTION
    if host.startswith(NON_PRODUCTION_PREFIXES) or host.endswith(NON_PRODUCTION_SUFFIXES):
        return NON_PRODUCTION
    if host in PRODUCTION_HOSTS:
        return PRODUCTION
    return UNKNOWN


def _normalize_host(host):
    host = (host or "").lower().strip()
    # Strip credentials and default ports.
    if "@" in host:
        host = host.rsplit("@", 1)[1]
    if host.endswith(":80") or host.endswith(":443"):
        host = host.rsplit(":", 1)[0]
    # www is not a distinct site here; both spellings serve the same pages.
    if host.startswith("www.") and host[4:] in PRODUCTION_HOSTS:
        host = host[4:]
    return host


def _normalize_path(path):
    if not path:
        return "/"
    # Collapse duplicate slashes without touching the rest of the path.
    while "//" in path:
        path = path.replace("//", "/")
    if not path.startswith("/"):
        path = "/" + path
    last = path.rsplit("/", 1)[-1]
    # WordPress serves directory-style URLs with a trailing slash; a file-like
    # last segment (sitemap.xml, robots.txt) must not gain one.
    if last and "." not in last and not path.endswith("/"):
        path += "/"
    return path


def canonicalize(url, default_origin=DEFAULT_ORIGIN):
    """Return the CanonicalUrl for any page identifier a source might emit.

    Accepts absolute URLs, protocol-relative URLs, and bare paths (GA4 reports
    paths, so this is the common case).
    """
    raw = "" if url is None else str(url).strip()

    if raw in GA4_NULL_VALUES:
        return CanonicalUrl(UNATTRIBUTED, "", "", "", UNKNOWN, [], raw)

    candidate = raw
    if candidate.startswith("//"):
        candidate = "https:" + candidate
    elif candidate.startswith("/"):
        candidate = default_origin.rstrip("/") + candidate
    elif "://" not in candidate:
        # A bare "molosoc.com/page" or a relative path.
        candidate = default_origin.rstrip("/") + "/" + candidate.lstrip("/")

    parts = urlsplit(candidate)
    scheme = (parts.scheme or "https").lower()
    if scheme == "http":
        scheme = "https"

    host = _normalize_host(parts.netloc)
    path = _normalize_path(parts.path)

    kept, dropped = [], []
    for name, value in parse_qsl(parts.query, keep_blank_values=True):
        if is_tracking_param(name):
            dropped.append(name)
        else:
            kept.append((name, value))
    # Stable ordering so two orderings of the same parameters are one identity.
    kept.sort()
    query = urlencode(kept)

    canonical = urlunsplit((scheme, host, path, query, ""))
    return CanonicalUrl(
        url=canonical,
        host=host,
        path=path,
        query=query,
        classification=classify_host(host),
        dropped_params=dropped,
        original=raw,
    )


def is_production_url(url, default_origin=DEFAULT_ORIGIN):
    return canonicalize(url, default_origin).is_production


class ExclusionReport:
    """What production filtering removed, so it is never a silent drop."""

    __slots__ = ("kept", "excluded", "by_host", "by_classification")

    def __init__(self, kept, excluded, by_host, by_classification):
        self.kept = kept
        self.excluded = excluded
        self.by_host = by_host
        self.by_classification = by_classification

    @property
    def excluded_count(self):
        return len(self.excluded)

    def summary(self):
        if not self.excluded:
            return "no non-production rows excluded"
        hosts = ", ".join(f"{host} x{n}" for host, n in sorted(self.by_host.items()))
        return f"excluded {len(self.excluded)} row(s) from: {hosts}"


def filter_production(rows, url_of=lambda row: row, default_origin=DEFAULT_ORIGIN,
                      keep_unknown=False):
    """Split rows into production and everything else.

    `keep_unknown=False` is the safe default for marketing analysis: a host
    nobody has classified should not silently contribute to reported numbers.
    The exclusions are returned, never discarded, so the count can be reported
    as a data-quality figure.
    """
    kept, excluded = [], []
    by_host, by_classification = Counter(), Counter()

    for row in rows:
        canonical = canonicalize(url_of(row), default_origin)
        allowed = canonical.is_production or (keep_unknown and canonical.classification == UNKNOWN)
        if allowed:
            kept.append(row)
        else:
            excluded.append(row)
            by_host[canonical.host or "(none)"] += 1
            by_classification[canonical.classification] += 1

    return ExclusionReport(kept, excluded, dict(by_host), dict(by_classification))
