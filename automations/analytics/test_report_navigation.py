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
    assert td.report_path(dash.CLIENT, "analytics") == f"/reports/{pub.PROJECT_DIR}/"


def test_every_sectioned_route_matches_a_section_the_publisher_allows():
    """A tab may only point at a directory `--section` can actually write."""
    for key, segment, _label in td.REPORTS:
        if segment and key in td.LIVE_REPORTS:
            assert segment in pub.ALLOWED_SECTIONS, key


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


def test_nothing_that_is_not_connected_is_a_link():
    bar = _bar()
    linked = {label for _href, _attrs, label in LINK.findall(bar)}
    assert linked == {"Analytics", "Growth"}
    assert bar.count('aria-disabled="true"') == len(td.REPORTS) - 2


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
