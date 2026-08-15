#!/usr/bin/env python3
"""
Offline tests for language preservation and conversion metrics.

Language matters here because the site runs Polylang with per-language slugs
and no language path prefix — the Czech product page and the English legal
pages both sit at the root. So a confident guess is often wrong, and every
record carries both a value and how it was determined. "und" is a correct
answer, not a failure.

Reporting is not split by language yet (volume is too low), but the history
has to support it later without re-collection.

Run with:  python3 -m pytest automations/analytics/
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import canonical_url as cu  # noqa: E402
import normalize as nz  # noqa: E402
from records import PAGE, SITE  # noqa: E402

COLLECTED_AT = "2026-08-14T17:34:03+00:00"


# --------------------------------------------------------------------------
# Language detection
# --------------------------------------------------------------------------

def test_language_path_prefix_wins():
    assert cu.detect_language("/cs/produkt/") == (cu.CZECH, cu.LANG_PATH_PREFIX)
    assert cu.detect_language("/en/product/") == (cu.ENGLISH, cu.LANG_PATH_PREFIX)


def test_polylang_cz_prefix_spelling_is_accepted():
    # The theme checks pll_current_language() === 'cz'.
    assert cu.detect_language("/cz/produkt/")[0] == cu.CZECH


def test_lang_query_parameter_is_used_when_present():
    assert cu.detect_language("/product/?lang=cs") == (cu.CZECH, cu.LANG_QUERY_PARAM)
    assert cu.detect_language("/product/?lang=en") == (cu.ENGLISH, cu.LANG_QUERY_PARAM)


def test_the_language_parameter_survives_canonicalization():
    # It identifies different content, so it must not be stripped as tracking.
    canonical = cu.canonicalize("/product/?lang=cs&fbclid=junk")
    assert "lang=cs" in canonical.url
    assert cu.detect_language(canonical)[0] == cu.CZECH


def test_known_czech_slugs_are_recognized_by_lexicon():
    for path in ("/obchodni-podminky/", "/zasady-dopravy/", "/vraceni-a-refundace/"):
        code, source = cu.detect_language(path)
        assert (code, source) == (cu.CZECH, cu.LANG_SLUG_LEXICON), path


def test_known_english_slugs_are_recognized_by_lexicon():
    for path in ("/terms-of-services/", "/refund-policy/", "/legal-disclaimer/"):
        code, source = cu.detect_language(path)
        assert (code, source) == (cu.ENGLISH, cu.LANG_SLUG_LEXICON), path


def test_the_real_czech_product_url_is_recognized():
    # From the verified GA4 and Search Console runs. The language lives in a
    # later path segment, not the first.
    code, source = cu.detect_language("/product/molosoc-hydratacni-navleky-na-nohy/")
    assert code == cu.CZECH
    assert source == cu.LANG_SLUG_LEXICON


def test_an_unrecognized_page_is_undetermined_not_guessed():
    code, source = cu.detect_language("/some-new-page/")
    assert code == cu.UNDETERMINED
    assert source == cu.LANG_UNDETERMINED


def test_the_homepage_is_undetermined():
    # Both languages share the root; claiming one would be wrong half the time.
    assert cu.detect_language("https://molosoc.com/")[0] == cu.UNDETERMINED


def test_unattributed_rows_are_undetermined():
    assert cu.detect_language("(not set)")[0] == cu.UNDETERMINED


def test_detection_accepts_an_already_canonical_url():
    canonical = cu.canonicalize("/obchodni-podminky/")
    assert cu.detect_language(canonical)[0] == cu.CZECH


# --------------------------------------------------------------------------
# Language on records
# --------------------------------------------------------------------------

GA4_RESULT = {
    "ok": True, "propertyId": "521643495",
    "dateRange": {"start": "2026-08-07", "end": "2026-08-13"},
    "users": 10, "sessions": 21, "views": 23,
    "landingPages": [
        {"landingPage": "/product/molosoc-hydratacni-navleky-na-nohy/",
         "sessions": 8, "activeUsers": 5},
        {"landingPage": "/terms-of-services/", "sessions": 2, "activeUsers": 2},
        {"landingPage": "/", "sessions": 8, "activeUsers": 5},
    ],
}

GSC_RESULT = {
    "ok": True, "siteUrl": "sc-domain:molosoc.com",
    "dateRange": {"start": "2026-08-05", "end": "2026-08-11"},
    "clicks": 1, "impressions": 8, "ctr": 0.125, "position": 8.0,
    "topQueries": [],
    "topPages": [{"page": "https://molosoc.com/obchodni-podminky/", "clicks": 0,
                  "impressions": 4, "ctr": 0.0, "position": 2.0}],
}


def pages(records):
    return [r for r in records if r.entity_type == PAGE]


def test_ga4_page_records_carry_language_and_its_source():
    rows = pages(nz.ga4_records(GA4_RESULT, COLLECTED_AT))
    czech = [r for r in rows if "hydratacni" in r.entity_id]
    assert czech and all(r.language == cu.CZECH for r in czech)
    assert all(r.language_source == cu.LANG_SLUG_LEXICON for r in czech)


def test_ga4_english_and_undetermined_pages_are_distinguished():
    rows = pages(nz.ga4_records(GA4_RESULT, COLLECTED_AT))
    by_language = {r.entity_id: r.language for r in rows}
    assert by_language["https://molosoc.com/terms-of-services/"] == cu.ENGLISH
    assert by_language["https://molosoc.com/"] == cu.UNDETERMINED


def test_gsc_page_records_carry_language():
    rows = pages(nz.gsc_records(GSC_RESULT, COLLECTED_AT))
    assert rows and all(r.language == cu.CZECH for r in rows)


def test_every_page_record_preserves_its_full_path_for_later_backfill():
    # Language can be re-derived once the Polylang URL mode is confirmed,
    # without re-collecting anything.
    rows = pages(nz.ga4_records(GA4_RESULT, COLLECTED_AT))
    assert all(r.notes.get("path") for r in rows)
    assert any(r.notes["path"] == "/terms-of-services/" for r in rows)


def test_clarity_page_records_carry_language():
    payload = [{"metricName": "PopularPages", "information": [
        {"url": "https://molosoc.com/obchodni-podminky/", "visitsCount": "5"},
        {"url": "https://molosoc.com/refund-policy/", "visitsCount": "3"}]}]
    rows = pages(nz.clarity_records(payload, date="2026-08-14", collected_at=COLLECTED_AT))
    by_language = {r.entity_id: r.language for r in rows}
    assert by_language["https://molosoc.com/obchodni-podminky/"] == cu.CZECH
    assert by_language["https://molosoc.com/refund-policy/"] == cu.ENGLISH


def test_non_page_records_have_no_language():
    # A country or browser row has no page and therefore no language.
    rows = nz.ga4_records(GA4_RESULT, COLLECTED_AT)
    site_rows = [r for r in rows if r.entity_type == SITE]
    assert site_rows and all(r.language is None for r in site_rows)


def test_language_survives_a_storage_round_trip():
    from records import MetricRecord

    row = pages(nz.ga4_records(GA4_RESULT, COLLECTED_AT))[0]
    assert MetricRecord.from_dict(row.to_dict()).language == row.language


# --------------------------------------------------------------------------
# Conversion metrics
# --------------------------------------------------------------------------

def test_the_approved_conversion_definitions():
    assert nz.HEADLINE_CONVERSION == "purchase"
    assert set(nz.SUPPORTING_FUNNEL_EVENTS) == {"begin_checkout", "add_to_cart"}
    assert nz.TRACKED_KEY_EVENTS[0] == "purchase"


def test_key_events_become_one_metric_each():
    result = dict(GA4_RESULT, keyEvents={"purchase": 3, "begin_checkout": 9,
                                         "add_to_cart": 21})
    rows = nz.ga4_records(result, COLLECTED_AT)
    by_metric = {r.metric: r.value for r in rows}

    assert by_metric["ga4_key_event_purchase"] == 3
    assert by_metric["ga4_key_event_begin_checkout"] == 9
    assert by_metric["ga4_key_event_add_to_cart"] == 21
    # Never a single blended "conversions" figure.
    assert "ga4_conversions" not in by_metric


def test_key_events_carry_sessions_as_their_denominator():
    result = dict(GA4_RESULT, keyEvents={"purchase": 3})
    row = [r for r in nz.ga4_records(result, COLLECTED_AT)
           if r.metric == "ga4_key_event_purchase"][0]
    assert row.sample_basis == 21  # site sessions, for a later conversion rate


def test_untracked_events_are_ignored():
    result = dict(GA4_RESULT, keyEvents={"purchase": 3, "scroll": 400})
    metrics = {r.metric for r in nz.ga4_records(result, COLLECTED_AT)}
    assert "ga4_key_event_purchase" in metrics
    assert "ga4_key_event_scroll" not in metrics


def test_absent_key_events_produce_no_records():
    # The current verified GA4 check does not report key events yet; that must
    # be a no-op, not a zero that reads as "no purchases".
    metrics = {r.metric for r in nz.ga4_records(GA4_RESULT, COLLECTED_AT)}
    assert not any(m.startswith("ga4_key_event_") for m in metrics)


def test_a_reported_zero_is_preserved_as_zero():
    result = dict(GA4_RESULT, keyEvents={"purchase": 0})
    row = [r for r in nz.ga4_records(result, COLLECTED_AT)
           if r.metric == "ga4_key_event_purchase"][0]
    assert row.value == 0
