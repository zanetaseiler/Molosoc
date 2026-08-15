#!/usr/bin/env python3
"""
Offline tests for URL canonicalization and host classification.

The cases that matter here came out of the live verification runs: GA4 split
the homepage across three rows because of Facebook click ids, and Search
Console returned staging URLs under the domain property. Both are covered
directly below.

Run with:  python3 -m pytest automations/analytics/
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import canonical_url as cu  # noqa: E402


# The exact values GA4 reported in the first verified run.
REAL_FBCLID_ROWS = [
    "/",
    "/?fbclid=IwcGRvZgRleHRuA2FlbQIxMQBzcnRjBmFwcF9pZAwyNTYyODEwNDA1NTgAAR5fe2qBx5N30"
    "YzpWhbz_MThh4Hwk195oiAh-tl1oFHuz_-TEaFmTSCv8Z2bNg_aem_MM6D0p9zBSOuxgFwWFYuTw",
    "/?fbclid=IwcGRvZgRleHRuA2FlbQIxMQBzcnRjBmFwcF9pZAwyNTYyODEwNDA1NTgAAR7halLLVFjQO"
    "uD8vw2D4GJHlJlfIsl75U0PjDEofdSkX6ym31sF8N1aJS_wJQ_aem_LbdFtcx8NeyUtEarxAvLRg",
]


# --------------------------------------------------------------------------
# Tracking parameters
# --------------------------------------------------------------------------

def test_the_three_real_ga4_homepage_rows_collapse_to_one_page():
    canonical = {cu.canonicalize(url).url for url in REAL_FBCLID_ROWS}
    assert canonical == {"https://molosoc.com/"}


def test_utm_family_is_stripped():
    url = ("/product/x/?utm_source=newsletter&utm_medium=email&utm_campaign=spring"
           "&utm_term=feet&utm_content=hero&utm_id=99")
    assert cu.canonicalize(url).url == "https://molosoc.com/product/x/"


def test_known_click_ids_are_stripped():
    for param in ("gclid", "fbclid", "msclkid", "ttclid", "srsltid", "mc_eid", "_ga"):
        result = cu.canonicalize(f"/page/?{param}=abc123")
        assert result.url == "https://molosoc.com/page/", param
        assert param in result.dropped_params


def test_dropped_parameters_are_reported_not_silently_removed():
    result = cu.canonicalize("/page/?fbclid=x&utm_source=y&lang=cs")
    assert sorted(result.dropped_params) == ["fbclid", "utm_source"]


def test_unknown_parameters_are_preserved():
    # Over-keeping splits one page in two and is visible; over-dropping fuses
    # two pages into one and is not. Unknown parameters are kept.
    result = cu.canonicalize("/shop/?lang=cs&variant=large&s=cracked+heels")
    assert "lang=cs" in result.url
    assert "variant=large" in result.url
    assert result.dropped_params == []


def test_polylang_language_parameter_survives():
    cs = cu.canonicalize("/product/x/?lang=cs&fbclid=junk")
    en = cu.canonicalize("/product/x/?lang=en")
    assert cs.url != en.url
    assert cs.url == "https://molosoc.com/product/x/?lang=cs"


def test_parameter_order_does_not_create_two_identities():
    a = cu.canonicalize("/x/?b=2&a=1")
    b = cu.canonicalize("/x/?a=1&b=2")
    assert a.url == b.url


# --------------------------------------------------------------------------
# Structure
# --------------------------------------------------------------------------

def test_bare_paths_from_ga4_get_the_site_origin():
    assert cu.canonicalize("/cracked-heels/").url == "https://molosoc.com/cracked-heels/"


def test_absolute_urls_from_search_console_are_unchanged_in_identity():
    assert cu.canonicalize("https://molosoc.com/cracked-heels/").url == \
        "https://molosoc.com/cracked-heels/"


def test_ga4_paths_and_gsc_urls_reach_the_same_identity():
    # This is the join the whole cross-source layer depends on.
    assert cu.canonicalize("/terms-of-services/").url == \
        cu.canonicalize("https://molosoc.com/terms-of-services/").url


def test_www_and_apex_are_one_host():
    assert cu.canonicalize("https://www.molosoc.com/x/").url == "https://molosoc.com/x/"


def test_http_is_normalized_to_https():
    assert cu.canonicalize("http://molosoc.com/x/").url.startswith("https://")


def test_fragments_are_dropped():
    assert cu.canonicalize("/x/#reviews").url == "https://molosoc.com/x/"


def test_trailing_slash_is_added_for_directory_style_paths():
    assert cu.canonicalize("/cracked-heels").url == "https://molosoc.com/cracked-heels/"


def test_file_like_paths_do_not_gain_a_trailing_slash():
    assert cu.canonicalize("/robots.txt").url == "https://molosoc.com/robots.txt"
    assert cu.canonicalize("/sitemap.xml").url == "https://molosoc.com/sitemap.xml"


def test_root_is_a_single_slash():
    assert cu.canonicalize("").url == cu.UNATTRIBUTED
    assert cu.canonicalize("https://molosoc.com").url == "https://molosoc.com/"


def test_duplicate_slashes_collapse():
    assert cu.canonicalize("//molosoc.com//a//b/").url == "https://molosoc.com/a/b/"


def test_default_ports_are_dropped():
    assert cu.canonicalize("https://molosoc.com:443/x/").host == "molosoc.com"


# --------------------------------------------------------------------------
# GA4 null-ish values
# --------------------------------------------------------------------------

def test_ga4_unattributed_rows_become_an_explicit_entity():
    # The verified run included a landing-page row with a blank value. It has
    # real sessions, so it is kept as an explicit entity, not dropped.
    for value in ("", "(not set)", "(none)", None):
        result = cu.canonicalize(value)
        assert result.url == cu.UNATTRIBUTED
        assert result.is_unattributed
        assert result.classification == cu.UNKNOWN


# --------------------------------------------------------------------------
# Host classification
# --------------------------------------------------------------------------

def test_production_hosts():
    assert cu.classify_host("molosoc.com") == cu.PRODUCTION
    assert cu.classify_host("www.molosoc.com") == cu.PRODUCTION


def test_the_real_staging_host_is_non_production():
    # Both URLs Search Console actually returned.
    for url in ("https://staging.molosoc.com/",
                "https://staging.molosoc.com/legal-disclaimer/"):
        assert cu.canonicalize(url).classification == cu.NON_PRODUCTION
        assert not cu.canonicalize(url).is_production


def test_common_non_production_prefixes_are_recognized():
    for host in ("dev.molosoc.com", "test.molosoc.com", "preview.molosoc.com",
                 "uat.molosoc.com", "stage.molosoc.com"):
        assert cu.classify_host(host) == cu.NON_PRODUCTION, host


def test_local_hosts_are_non_production():
    assert cu.classify_host("molosoc.local") == cu.NON_PRODUCTION
    assert cu.classify_host("site.test") == cu.NON_PRODUCTION


def test_unfamiliar_hosts_are_unknown_not_assumed_production():
    # An unclassified host must surface for a decision, not quietly count.
    assert cu.classify_host("cdn.example.com") == cu.UNKNOWN
    assert cu.canonicalize("https://example.com/x/").classification == cu.UNKNOWN


def test_staging_urls_still_canonicalize_correctly():
    result = cu.canonicalize("https://staging.molosoc.com/x?fbclid=junk")
    assert result.url == "https://staging.molosoc.com/x/"
    assert result.classification == cu.NON_PRODUCTION


# --------------------------------------------------------------------------
# Production filtering
# --------------------------------------------------------------------------

def test_filter_production_separates_and_counts_exclusions():
    rows = [
        "https://molosoc.com/",
        "https://molosoc.com/product/molosoc-hydratacni-navleky-na-nohy/",
        "https://molosoc.com/terms-of-services/",
        "https://staging.molosoc.com/",
        "https://staging.molosoc.com/legal-disclaimer/",
    ]
    report = cu.filter_production(rows)

    assert len(report.kept) == 3
    assert report.excluded_count == 2
    assert report.by_host == {"staging.molosoc.com": 2}
    assert "staging.molosoc.com x2" in report.summary()


def test_filter_production_excludes_unknown_hosts_by_default():
    report = cu.filter_production(["https://example.com/x/"])
    assert report.kept == []
    assert report.by_classification == {cu.UNKNOWN: 1}


def test_filter_production_can_keep_unknown_hosts_when_asked():
    report = cu.filter_production(["https://example.com/x/"], keep_unknown=True)
    assert len(report.kept) == 1


def test_filter_production_reads_urls_out_of_structures():
    rows = [{"page": "https://molosoc.com/"}, {"page": "https://staging.molosoc.com/"}]
    report = cu.filter_production(rows, url_of=lambda r: r["page"])
    assert report.kept == [{"page": "https://molosoc.com/"}]


def test_no_exclusions_reports_cleanly():
    report = cu.filter_production(["https://molosoc.com/"])
    assert report.excluded_count == 0
    assert "no non-production" in report.summary()
