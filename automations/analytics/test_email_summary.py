#!/usr/bin/env python3
"""
The Email Marketing card on the weekly dashboard.

Two things are being protected here, and both are about a summary telling the
truth in less space than the full report has.

**An unmeasured figure must not become a zero.** The email contract goes to
considerable trouble to keep "we could not see it" and "there was none" apart;
this card is the last step before a client reads the number, and flattening
them here would undo all of it on the page most people actually open.

**The card must read the artifact, not the page.** A dashboard that scraped the
email report for numbers would empty itself the first time that report's layout
changed, and would do it silently.

Run with:  python3 -m pytest automations/analytics/
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dashboard as dash  # noqa: E402
import email_summary as es  # noqa: E402

REPORT_URL = "https://trafficdom.com/reports/molosoc/email-marketing/"


def document(**overrides):
    """A published email document, in the shape the orchestrator emits."""
    base = {
        "kind": "molosoc.email_marketing_weekly",
        "schema_version": "1.0.0",
        "client_id": "molosoc",
        "generated_at": "2026-08-19T06:15:00+00:00",
        "period": {"start": "2026-08-10", "end": "2026-08-16"},
        "channel": {
            "counts": {
                "sent": 412, "delivered": 402, "bounced": 10,
                "unique_clicks": 37, "unsubscribes": 3,
                "orders": {"value": None, "basis": "unavailable",
                           "note": "no attribution", "unit": "count"},
                "revenue": {"value": None, "basis": "unavailable",
                            "note": "no attribution", "unit": "currency"},
            },
            "previous_counts": {"sent": 388, "delivered": 379,
                                "unique_clicks": 41, "unsubscribes": 2},
        },
        "automations": [],
        "observations": [
            {"id": "w", "severity": "watch", "headline": "A watch item."},
            {"id": "c", "severity": "concern", "headline": "A concern."},
        ],
        "recommendations": [
            {"id": "r1", "action": "monitor", "headline": "Watch it",
             "because": "b", "subject": "channel"},
            {"id": "r2", "action": "investigate", "headline": "Look into it",
             "because": "b", "subject": "channel"},
        ],
        "coverage": {"state": "partial", "notes": [],
                     "unavailable_metrics": ["orders", "revenue"]},
        "source": {"platform": "brevo", "read_only": True},
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------
# An absence is never a zero
# --------------------------------------------------------------------------

def test_an_unavailable_figure_renders_as_words_not_as_zero():
    html = es.email_section(document(), REPORT_URL)
    assert "Not available" in html
    assert ">0.00<" not in html


def test_it_says_why_the_figure_is_missing():
    html = es.email_section(document(), REPORT_URL)
    assert "Not reported for this account" in html


def test_a_genuine_zero_is_still_a_zero():
    """Nobody clicked is a result. It must not read as a reporting gap."""
    doc = document()
    doc["channel"]["counts"]["unique_clicks"] = 0
    html = es.email_section(doc, REPORT_URL)
    assert "0.0%" in html


def test_a_rate_with_no_denominator_is_unavailable_rather_than_zero():
    doc = document()
    doc["channel"]["counts"]["delivered"] = 0
    doc["channel"]["counts"]["unique_clicks"] = 0
    assert es._rate(doc, "click_rate") is None


def test_an_unavailable_entry_never_yields_a_number():
    assert es._value({"value": None, "basis": "unavailable", "note": "x"}) is None
    assert es._value({"value": 0, "basis": "unavailable", "note": "x"}) is None


def test_a_bare_number_is_read_as_a_measurement():
    assert es._value(5) == 5.0
    assert es._value(0) == 0.0


def test_a_boolean_is_not_a_measurement():
    assert es._value(True) is None


# --------------------------------------------------------------------------
# It is a summary
# --------------------------------------------------------------------------

def test_it_shows_four_decision_useful_figures():
    html = es.email_section(document(), REPORT_URL)
    for label in ("Delivered", "Click rate", "Unsubscribe rate", "Revenue"):
        assert label in html


def test_it_shows_only_the_strongest_observation():
    html = es.email_section(document(), REPORT_URL)
    assert "A concern." in html
    assert "A watch item." not in html


def test_it_shows_the_most_urgent_recommendation_only():
    html = es.email_section(document(), REPORT_URL)
    assert "Look into it" in html
    assert "Watch it" not in html


def test_it_shows_the_period_and_how_it_moved():
    html = es.email_section(document(), REPORT_URL)
    assert "2026-08-10 to 2026-08-16" in html
    assert "vs previous period" in html


def test_a_first_period_claims_no_movement():
    doc = document()
    doc["channel"].pop("previous_counts")
    html = es.email_section(doc, REPORT_URL)
    assert "vs previous period" not in html


def test_it_links_to_the_full_report():
    html = es.email_section(document(), REPORT_URL)
    assert REPORT_URL in html
    assert "Open the full Email Marketing report" in html


def test_it_does_not_duplicate_the_full_report():
    """No automation detail, no language split, no per-message table."""
    doc = document()
    doc["automations"] = [{"id": "welcome", "name": "Welcome",
                           "stage": "welcome", "state": "active",
                           "counts": {"sent": 10},
                           "segments": {"cs": {"counts": {"sent": 10}}}}]
    html = es.email_section(doc, REPORT_URL)
    assert "Welcome" not in html
    assert "— by language" not in html


def test_the_link_url_never_comes_from_the_document():
    """A URL inside an artifact is untrusted input pointing wherever it likes."""
    doc = document()
    doc["report_url"] = "https://example.invalid/attacker/"
    html = es.email_section(doc, REPORT_URL)
    assert "example.invalid" not in html


# --------------------------------------------------------------------------
# No document at all
# --------------------------------------------------------------------------

def test_no_document_says_so_rather_than_showing_nothing():
    html = es.email_section(None, REPORT_URL)
    assert "not yet publishing evidence" in html


def test_not_connected_is_distinguished_from_sent_nothing():
    doc = document()
    doc["channel"]["counts"] = {"sent": 0, "delivered": 0}
    doc["observations"] = [{"id": "n", "severity": "concern",
                            "headline": "No marketing email was sent."}]
    html = es.email_section(doc, REPORT_URL)
    assert "No marketing email was sent." in html
    assert "not yet publishing evidence" not in html


def test_an_empty_or_malformed_document_falls_back_safely():
    for value in ({}, [], "", None, "not a document"):
        assert "not yet publishing evidence" in es.email_section(value, REPORT_URL)


def test_a_missing_file_is_not_an_error(tmp_path):
    assert es.load(str(tmp_path / "nothing.json")) is None
    assert es.load(None) is None


def test_a_malformed_file_is_not_an_error(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert es.load(str(path)) is None


def test_a_file_without_a_kind_is_refused(tmp_path):
    path = tmp_path / "no-kind.json"
    path.write_text(json.dumps({"period": {}}), encoding="utf-8")
    assert es.load(str(path)) is None


def test_a_real_document_loads(tmp_path):
    path = tmp_path / "email.json"
    path.write_text(json.dumps(document()), encoding="utf-8")
    assert es.load(str(path))["kind"].endswith("email_marketing_weekly")


# --------------------------------------------------------------------------
# Following the pointer
# --------------------------------------------------------------------------

class Store:
    def __init__(self, objects):
        self.objects = objects
        self.requested = []

    def get_json(self, key):
        self.requested.append(key)
        if key not in self.objects:
            raise KeyError(key)
        return self.objects[key]


def test_it_follows_the_pointer_with_two_reads_and_no_listing():
    key = "reports/email/data/2026/08/2026-08-16/email.json"
    store = Store({es.POINTER_KEY: {"json_key": key}, key: document()})
    assert es.fetch(store)["kind"].endswith("email_marketing_weekly")
    assert store.requested == [es.POINTER_KEY, key]


def test_a_pointer_naming_anything_else_is_refused():
    """The key arrives inside a document, so it is input, not instruction."""
    for bad in ("reports/weekly/data/2026/report.json",
                "state/recommendations/ledger.json",
                "../../etc/passwd",
                "reports/email/data/report.md",
                "/reports/email/data/x.json"):
        store = Store({es.POINTER_KEY: {"json_key": bad}})
        with pytest.raises(es.PointerRefused):
            es.fetch(store)


def test_a_missing_pointer_costs_the_card_not_the_report():
    assert es.fetch(Store({})) is None


def test_a_pointer_that_names_a_missing_document_costs_the_card_only():
    store = Store({es.POINTER_KEY: {
        "json_key": "reports/email/data/2026/08/2026-08-16/email.json"}})
    assert es.fetch(store) is None


# --------------------------------------------------------------------------
# The dashboard integration
# --------------------------------------------------------------------------

def test_the_dashboard_renders_the_card_when_a_document_exists():
    page = dash.render_dashboard(dash.document_from_fixture("low_volume"),
                                 email=document())
    assert "Email marketing" in page
    assert REPORT_URL in page


def test_the_dashboard_renders_without_one():
    page = dash.render_dashboard(dash.document_from_fixture("low_volume"))
    assert "Email marketing" in page
    assert "not yet publishing evidence" in page


def test_the_existing_sections_are_unchanged_either_way():
    with_email = dash.render_dashboard(dash.document_from_fixture("low_volume"),
                                       email=document())
    without = dash.render_dashboard(dash.document_from_fixture("low_volume"))
    for heading in ("Traffic", "Search", "Behaviour",
                    "Ecommerce and conversions", "Recommendations"):
        assert heading in with_email
        assert heading in without


def test_the_email_card_sits_after_the_analytics_sections():
    """Compared on section anchors: the word "Recommendations" also appears as
    a label in the summary card at the top of the page."""
    page = dash.render_dashboard(dash.document_from_fixture("low_volume"),
                                 email=document())
    assert page.index('id="ecommerce"') < page.index('id="email"')
    assert page.index('id="email"') < page.index('id="recommendations"')


def test_the_header_names_email_as_a_source_only_when_there_is_one():
    with_email = dash.render_dashboard(dash.document_from_fixture("low_volume"),
                                       email=document())
    without = dash.render_dashboard(dash.document_from_fixture("low_volume"))
    assert "Clarity, Email" in with_email
    assert "Clarity, Email" not in without


def test_the_page_stays_self_contained():
    """Nothing is FETCHED from a network. The page quotes plenty of URLs — the
    client's own pages, in the analytics tables — and quoting one is not
    fetching it. What matters is that no element loads a remote resource."""
    page = dash.render_dashboard(dash.document_from_fixture("low_volume"),
                                 email=document())
    assert "<script" not in page
    assert "<link" not in page
    assert "src=" not in page
    # The one <a href> is the link to the sibling report, which is the point of
    # the card. It is a destination, not a resource the page loads.
    assert page.count("href=") == 1
    assert f'href="{REPORT_URL}"' in page
