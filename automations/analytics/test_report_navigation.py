"""
The report navigation, as this repository renders it.

The bar itself belongs to the shared design system and is tested there. What
has to be true HERE is the half that only this repository knows:

* the client id the tabs are built from is the directory the publisher writes
  to, so every route lands where a file is actually put;
* the Analytics report marks itself as the active tab;
* the bar reaches the rendered page, inside the masthead, once; and
* this repository writes no navigation markup of its own — the whole point of
  vendoring the design system is that there is one implementation.
"""

import re

import dashboard as dash
import publish_dashboard as pub
import trafficdom_design as td

LINK = re.compile(r'<a href="([^"]+)"([^>]*)>([^<]+)</a>')
NAV = re.compile(r'<nav class="td-nav".*?</nav>', re.S)


def _page():
    return dash.render_dashboard(dash.document_from_fixture("low_volume"))


def _bar(page=None):
    found = NAV.search(page if page is not None else _page())
    return found.group(0) if found else ""


def test_the_client_the_tabs_use_is_the_directory_we_publish_to():
    """The one agreement this repository owns. Break it and every tab 404s."""
    assert dash.CLIENT == pub.PROJECT_DIR


def test_the_analytics_route_is_where_this_report_is_published():
    """Since the client-first cutover (ADR 0043 in the Growth Engine
    repository), the Analytics report has its own segment — the client
    root now belongs to the Brand Overview instead."""
    assert (td.report_path(dash.CLIENT, "analytics")
           == f"/reports/{pub.PROJECT_DIR}/analytics/")
    assert "analytics" in pub.ALLOWED_SECTIONS[pub.PROJECT_DIR]


def test_every_sectioned_route_matches_a_section_the_publisher_allows():
    """A tab may only point at a directory `--section` can actually write.

    Checked against this repository's own live set (`dash.
    CLIENT_LIVE_REPORTS`) rather than the bundle's shared default: that is
    the set this render actually uses, and the property this test exists to
    hold — a live tab always has somewhere real to land — has to hold for
    it specifically."""
    for key, segment, _label in td.REPORTS:
        if segment and key in dash.CLIENT_LIVE_REPORTS:
            assert segment in pub.ALLOWED_SECTIONS[pub.PROJECT_DIR], key


def test_the_page_carries_the_bar():
    assert _bar()


def test_it_sits_inside_the_masthead():
    header = re.search(r'<header class="td-header".*?</header>', _page(), re.S)
    assert header and '<nav class="td-nav"' in header.group(0)


def test_analytics_is_the_active_tab():
    current = [label for _href, attrs, label in LINK.findall(_bar())
               if "aria-current" in attrs]
    assert current == ["Analytics"]


def test_growth_is_reachable_from_here():
    hrefs = [href for href, _attrs, _label in LINK.findall(_bar())]
    assert f"/reports/{dash.CLIENT}/growth/" in hrefs


def test_paid_ads_is_reachable_from_here():
    """dashboard.py now opts into its own live set (dash.
    CLIENT_LIVE_REPORTS), which includes `paid` now that
    publish-paid-ads-report.yml actually publishes that page — the
    established per-client `live=` mechanism (ADR 0043 in the Growth Engine
    repository; see `report_header`'s own docstring there), not a new one
    invented for this."""
    hrefs = [href for href, _attrs, _label in LINK.findall(_bar())]
    assert f"/reports/{dash.CLIENT}/paid/" in hrefs


def test_nothing_that_is_not_a_published_section_is_a_link():
    """dashboard.py now calls report_header() with an explicit `live=`
    (dash.CLIENT_LIVE_REPORTS) rather than falling back to the bundle's own
    shared default, because this client's actually-published set differs
    from it: Paid Ads is live here, published through the same
    publish_dashboard.py --section mechanism as Growth and Email Marketing.

    Social stays unlinked — no MOLOSOC Social report has been published
    through this publisher (only Zoe's has, at reports/zoe/social/) — and
    this assertion is exactly what stops that from silently drifting: a tab
    may not go live here before its page does."""
    bar = _bar()
    linked = {label for _href, _attrs, label in LINK.findall(bar)}
    assert linked == {"Overview", "Analytics", "Growth", "Email Marketing", "Paid"}
    assert bar.count('aria-disabled="true"') == (
        len(td.REPORTS) - len(dash.CLIENT_LIVE_REPORTS))


def test_there_is_exactly_one_navigation_on_the_page():
    assert _page().count('<nav class="td-nav"') == 1


def test_the_brand_mark_survives_above_it():
    header = re.search(r'<header class="td-header".*?</header>',
                       _page(), re.S).group(0)
    assert header.index("td-wordmark") < header.index("td-nav")


def test_this_repository_writes_no_navigation_of_its_own():
    """One implementation. A second one here is how the two bars would drift."""
    source = (dash.__file__ and open(dash.__file__, encoding="utf-8").read())
    assert "<nav" not in source
    assert "td-nav" not in source


def test_the_bar_adds_no_remote_resource():
    for href, _attrs, _label in LINK.findall(_bar()):
        assert href.startswith("/reports/"), href
