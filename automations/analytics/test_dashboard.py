#!/usr/bin/env python3
"""
Offline tests for the HTML dashboard and its FTPS publisher.

Two things carry real risk here and both are asserted hard:

  1. The page must not promote a recommendation the analysis engine withheld,
     and must never let a missing comparison read as a zero. It is a second
     view of the same report, so a divergence between it and the Markdown is a
     defect by definition.
  2. The publisher writes to a host that also serves a live WordPress site.
     The destination is derived, never free text, and the tests below try to
     push it somewhere it should refuse to go.

Everything runs offline: no network, no credentials, no FTP server.

Run with:  python3 -m pytest automations/analytics/
"""

import datetime as dt
import ftplib
import ssl
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import clarity_api  # noqa: E402
import dashboard as dash  # noqa: E402
import publish_dashboard as pub  # noqa: E402
import report_store as rs  # noqa: E402
from analysis_model import INSUFFICIENT_DATA, PRIORITY_MONITOR  # noqa: E402

BASE = "/public_html/Trafficdom.com/reports"
EXPECTED_DIR = "/public_html/Trafficdom.com/reports/molosoc"


@pytest.fixture(autouse=True)
def no_live_clarity(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("the dashboard must never call the Clarity API")

    monkeypatch.setattr(clarity_api, "fetch_live_insights", forbidden)
    monkeypatch.setattr(clarity_api, "load_api_token", forbidden)


@pytest.fixture(scope="module")
def low_volume():
    return dash.document_from_fixture("low_volume")


@pytest.fixture(scope="module")
def healthy():
    return dash.document_from_fixture("healthy")


# --------------------------------------------------------------------------
# The page renders, offline, from stored data alone
# --------------------------------------------------------------------------

def test_the_page_renders_a_complete_html_document(healthy):
    page = dash.render_dashboard(healthy)

    assert page.startswith("<!doctype html>")
    assert page.rstrip().endswith("</html>")
    assert '<meta name="viewport"' in page


def test_the_page_is_self_contained(healthy):
    """No CDN, no external stylesheet, no script. It must open offline."""
    page = dash.render_dashboard(healthy)

    assert "<script" not in page.lower()
    assert "http://" not in page
    assert not re.search(r'<link[^>]+stylesheet', page)
    assert "cdnjs" not in page and "googleapis" not in page


def test_every_required_section_is_present(healthy):
    page = dash.render_dashboard(healthy)

    for heading in ("Executive summary", "Traffic — GA4", "Search Console — SEO",
                    "Behaviour — Clarity", "Ecommerce and conversions",
                    "Recommendations", "Readiness and data quality"):
        assert heading in page, heading


def test_the_page_shows_current_and_previous_period(healthy):
    page = dash.render_dashboard(healthy)

    assert healthy["period"]["start"] in page
    assert healthy["period"]["end"] in page
    assert healthy["comparison_period"]["start"] in page
    assert healthy["comparison_period"]["end"] in page


def test_headline_numbers_come_through(healthy):
    page = dash.render_dashboard(healthy)
    assert "840" in page      # GA4 sessions
    assert "6,300" in page    # GSC impressions


def test_the_page_asks_not_to_be_indexed(healthy):
    # It will sit on a public web host at a guessable path.
    page = dash.render_dashboard(healthy)
    assert 'name="robots"' in page and "noindex" in page


def test_the_page_states_it_changed_nothing(healthy):
    assert "No change has been made to the site" in dash.render_dashboard(healthy)


# --------------------------------------------------------------------------
# The readiness gate holds in the view
# --------------------------------------------------------------------------

def test_low_volume_shows_no_recommendations_and_says_why(low_volume):
    page = dash.render_dashboard(low_volume)

    assert low_volume["readiness"] == INSUFFICIENT_DATA
    assert "withheld recommendations at this volume" in page
    assert "Nothing has been applied to the site" in page


def test_the_page_renders_only_recommendations_the_engine_produced(healthy):
    page = dash.render_dashboard(healthy)

    for rec in healthy["recommendations"]:
        assert rec["action"][:40] in page
    # Count the rendered cards; the view must not invent an extra one.
    assert page.count('class="ms-rec ') == len(healthy["recommendations"])


def test_the_view_cannot_promote_a_monitor_recommendation(low_volume):
    # Everything at low volume is Monitor, and no card may render as High.
    # Match the applied class, not the CSS rule that declares it.
    assert all(r["priority"] == PRIORITY_MONITOR
               for r in low_volume["recommendations"])
    page = dash.render_dashboard(low_volume)

    applied = set(re.findall(r'class="ms-rec ms-rec--(\w+)"', page))
    assert "high" not in applied
    assert "medium" not in applied


# --------------------------------------------------------------------------
# A missing comparison must never read as zero
# --------------------------------------------------------------------------

def test_an_unmeasured_comparison_is_explained_not_dashed(healthy):
    """Pre-boundary conversions have no comparison. The reason is in the
    report, so the card must show it rather than an unexplained dash."""
    conversions = [f for f in healthy["facts"]
                   if f["metric"] == "ga4_key_event_purchase"]
    assert conversions and conversions[0]["comparison_value"] is None

    page = dash.render_dashboard(healthy)
    assert "Previous period unmeasured" in page
    assert "unmeasured, not zero sales" in page


def test_the_ecommerce_boundary_is_stated_on_the_page(healthy):
    page = dash.render_dashboard(healthy)
    assert "predate ecommerce tracking" in page
    assert "not an absence of sales" in page


def test_a_rise_in_average_position_is_not_shown_as_an_improvement():
    """Position 8 -> 12 is worse, however the arithmetic reads."""
    worse = {"metric": "gsc_position", "period_value": 12.0,
             "comparison_value": 8.0, "delta_abs": 4.0, "delta_pct": 0.5}
    better = {"metric": "gsc_position", "period_value": 6.0,
              "comparison_value": 8.0, "delta_abs": -2.0, "delta_pct": -0.25}

    assert dash.change_direction(worse) == "down"
    assert dash.change_direction(better) == "up"


def test_a_rise_in_bot_share_is_not_shown_as_an_improvement():
    fact = {"metric": "clarity_bot_share", "period_value": 0.4,
            "comparison_value": 0.1, "delta_abs": 0.3, "delta_pct": 3.0}
    assert dash.change_direction(fact) == "down"


def test_a_fact_below_minimum_sample_is_flagged(healthy):
    page = dash.render_dashboard(healthy)
    assert "below minimum sample" in page or "low sample" in page


# --------------------------------------------------------------------------
# Data quality is visible
# --------------------------------------------------------------------------

def test_data_quality_and_coverage_reach_the_page(healthy):
    page = dash.render_dashboard(healthy)

    assert "Readiness and data quality" in page
    assert "Tracking coverage (GA4 vs Clarity)" in page
    assert "not a consent rate" in page       # the caveat survives into the view


def test_the_readiness_state_is_shown_as_a_badge(low_volume):
    page = dash.render_dashboard(low_volume)
    assert "ms-badge--warn" in page
    assert "insufficient data" in page


# --------------------------------------------------------------------------
# Trends
# --------------------------------------------------------------------------

def _index_with(weeks):
    entries = []
    for i in range(weeks):
        day = dt.date(2026, 8, 14) + dt.timedelta(days=7 * i)
        entries.append({"report_date": day.isoformat(),
                        "headline_metrics": {"ga4_sessions": 100 + i * 10,
                                             "gsc_clicks": 5 + i}})
    return {"entries": list(reversed(entries))}


def test_no_trend_section_until_there_is_a_shape_to_see(healthy):
    # One or two weeks is not a trend; drawing one would be a lie by chart.
    assert "id=\"trends\"" not in dash.render_dashboard(healthy, index=_index_with(2))
    assert "id=\"trends\"" not in dash.render_dashboard(healthy, index=None)


def test_the_trend_section_appears_once_enough_weeks_exist(healthy):
    page = dash.render_dashboard(healthy, index=_index_with(6))
    assert 'id="trends"' in page
    assert "<svg" in page and "polyline" in page
    assert "6 weekly reports" in page


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def test_the_cli_writes_a_file_from_a_fixture(tmp_path):
    out = tmp_path / "index.html"
    assert dash.main(["--fixture", "low_volume", "--out", str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_the_cli_renders_a_stored_report_document(tmp_path, healthy):
    import json

    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(healthy), encoding="utf-8")
    out = tmp_path / "index.html"

    assert dash.main(["--report", str(report_path), "--out", str(out)]) == 0
    assert "Executive summary" in out.read_text(encoding="utf-8")


def test_a_missing_index_costs_the_trend_strip_not_the_page(tmp_path):
    out = tmp_path / "index.html"
    code = dash.main(["--fixture", "healthy", "--out", str(out),
                      "--index", str(tmp_path / "nope.json")])
    assert code == 0
    assert "Executive summary" in out.read_text(encoding="utf-8")


def test_rendering_is_deterministic(healthy):
    stamp = "2026-08-19T06:30:00+00:00"
    assert (dash.render_dashboard(healthy, generated_at=stamp)
            == dash.render_dashboard(healthy, generated_at=stamp))


def test_report_values_are_html_escaped():
    document = {
        "report_date": "2026-08-14", "period": {}, "comparison_period": {},
        "readiness": "ready", "readiness_note": '<img src=x onerror="alert(1)">',
        "facts": [], "recommendations": [], "data_quality": {},
        "source_coverage": {}, "conversions": {}, "tracking_coverage": {},
        "ecommerce_tracking_boundary": {},
    }
    page = dash.render_dashboard(document)

    assert "<img src=x" not in page
    assert "&lt;img src=x" in page


# --------------------------------------------------------------------------
# Publisher: the destination is derived, never free text
# --------------------------------------------------------------------------

def test_the_remote_directory_is_the_molosoc_folder_under_the_base_path():
    assert pub.resolve_remote_dir(BASE) == EXPECTED_DIR
    assert pub.resolve_remote_dir(BASE + "/") == EXPECTED_DIR


def test_an_unset_base_path_falls_back_to_the_committed_default():
    """The variable was unset on the first deployment attempt. A default keeps
    that from silently becoming a missing dashboard every week — and the
    guards below still apply to it."""
    for value in (None, "", "   "):
        assert pub.resolve_remote_dir(value) == EXPECTED_DIR
    assert pub.DEFAULT_BASE_PATH == BASE


def test_the_variable_overrides_the_default():
    assert pub.resolve_remote_dir("/srv/other/reports") == "/srv/other/reports/molosoc"


def test_a_relative_base_path_is_refused():
    with pytest.raises(pub.PublishError, match="absolute"):
        pub.resolve_remote_dir("public_html/reports")


def test_a_traversing_base_path_is_refused():
    with pytest.raises(pub.PublishError, match="relative segments"):
        pub.resolve_remote_dir("/public_html/../../etc")


def test_a_wordpress_path_is_refused():
    for bad in ("/public_html/wp-content/uploads", "/srv/site/wp-admin",
                "/var/www/wp-includes/x"):
        with pytest.raises(pub.PublishError, match="WordPress"):
            pub.resolve_remote_dir(bad)


def test_the_resolved_path_always_ends_in_the_project_directory():
    assert pub.resolve_remote_dir("/a/b").endswith("/molosoc")
    assert pub.PROJECT_DIR == "molosoc"


def test_only_index_html_may_be_uploaded():
    with pytest.raises(pub.PublishError, match="refusing to upload"):
        pub.upload(object(), "whatever.html", remote_filename="shell.php")


# --------------------------------------------------------------------------
# Publisher: the server's own PWD is what gets checked
# --------------------------------------------------------------------------

class FakeFTP:
    """Enough of ftplib.FTP_TLS to drive the guards."""

    def __init__(self, cwd="/", dirs=(), fail_cwd=()):
        self._cwd = cwd
        self._dirs = set(dirs)
        self._fail_cwd = set(fail_cwd)
        self.stored = []
        self.made = []

    def cwd(self, path):
        target = path if path.startswith("/") else f"{self._cwd.rstrip('/')}/{path}"
        if target in self._fail_cwd or target not in self._dirs:
            raise ftplib.error_perm(f"550 {target}: No such file or directory")
        self._cwd = target

    def pwd(self):
        return self._cwd

    def mkd(self, name):
        target = f"{self._cwd.rstrip('/')}/{name}"
        self._dirs.add(target)
        self.made.append(target)

    def storbinary(self, command, handle):
        self.stored.append((command, self._cwd, handle.read()))

    def voidcmd(self, _command):
        return "200"

    def size(self, _name):
        return len(self.stored[-1][2]) if self.stored else None


def test_the_upload_is_abandoned_when_the_server_reports_a_different_directory():
    """A chroot or a symlink can land a locally-correct path elsewhere.
    Only PWD reveals it, so PWD is what decides."""
    ftps = FakeFTP(cwd="/public_html/someone-elses-site")

    with pytest.raises(pub.PublishError) as excinfo:
        pub.verify_location(ftps, EXPECTED_DIR)

    assert "FAILED" in str(excinfo.value)
    assert "Nothing was uploaded" in str(excinfo.value)
    assert not ftps.stored


def test_the_location_check_passes_on_the_expected_directory():
    ftps = FakeFTP(cwd=EXPECTED_DIR)
    assert pub.verify_location(ftps, EXPECTED_DIR) == EXPECTED_DIR


def test_a_chrooted_account_reporting_a_shorter_path_still_verifies():
    # Some hosts chroot to the account root, so PWD is /reports/molosoc.
    ftps = FakeFTP(cwd="/reports/molosoc")
    assert pub.verify_location(ftps, EXPECTED_DIR) == "/reports/molosoc"


def test_a_sibling_project_directory_is_rejected():
    ftps = FakeFTP(cwd="/public_html/Trafficdom.com/reports/othersite")
    with pytest.raises(pub.PublishError):
        pub.verify_location(ftps, EXPECTED_DIR)


def test_a_missing_base_path_is_an_error_rather_than_a_directory_to_invent():
    """A typo in the base path must not create a folder in someone's web root."""
    ftps = FakeFTP(cwd="/", dirs={"/"})

    with pytest.raises(pub.PublishError, match="does not exist or is not reachable"):
        pub.enter_remote_dir(ftps, EXPECTED_DIR)
    assert not ftps.made


def test_only_the_project_directory_is_ever_created():
    ftps = FakeFTP(cwd="/", dirs={"/", BASE})

    entered = pub.enter_remote_dir(ftps, EXPECTED_DIR)

    assert entered == EXPECTED_DIR
    assert ftps.made == [EXPECTED_DIR], "nothing above the project dir may be created"


def test_an_existing_project_directory_is_entered_without_being_recreated():
    ftps = FakeFTP(cwd="/", dirs={"/", BASE, EXPECTED_DIR})
    assert pub.enter_remote_dir(ftps, EXPECTED_DIR) == EXPECTED_DIR
    assert ftps.made == []


def test_the_upload_stores_exactly_one_file_in_the_verified_directory(tmp_path):
    page = tmp_path / "index.html"
    page.write_text("<!doctype html><html></html>", encoding="utf-8")
    ftps = FakeFTP(cwd="/", dirs={"/", BASE, EXPECTED_DIR})
    pub.enter_remote_dir(ftps, EXPECTED_DIR)
    pub.verify_location(ftps, EXPECTED_DIR)

    sent = pub.upload(ftps, str(page))

    assert len(ftps.stored) == 1
    command, cwd, _body = ftps.stored[0]
    assert command == "STOR index.html"
    assert cwd == EXPECTED_DIR
    assert pub.confirm_uploaded(ftps, sent) == (sent, None)


def test_a_size_mismatch_is_reported_rather_than_passed_over(tmp_path):
    page = tmp_path / "index.html"
    page.write_text("<!doctype html>", encoding="utf-8")
    ftps = FakeFTP(cwd="/", dirs={"/", BASE, EXPECTED_DIR})
    pub.enter_remote_dir(ftps, EXPECTED_DIR)
    pub.upload(ftps, str(page))

    _size, problem = pub.confirm_uploaded(ftps, 999999)
    assert "size mismatch" in problem


def test_the_publisher_never_deletes_or_renames():
    source = Path(pub.__file__).read_text(encoding="utf-8")
    for destructive in (".delete(", ".rmd(", ".rename(", "DELE ", "RMD ", "RNFR "):
        assert destructive not in source, destructive


def test_missing_credentials_stop_the_run_before_connecting():
    env = {"REPORTS_BASE_PATH": BASE}
    with pytest.raises(pub.PublishError, match="missing required secret"):
        pub.load_settings(env)


def test_the_password_is_registered_for_redaction():
    import analytics_common

    analytics_common.reset_secrets()
    try:
        pub.load_settings({"REPORTS_SFTP_HOST": "ftp.example.com",
                           "REPORTS_SFTP_USER": "reports",
                           "REPORTS_SFTP_PASS": "hunter2-secret",
                           "REPORTS_BASE_PATH": BASE})
        assert "hunter2-secret" not in analytics_common.redact(
            "login failed for hunter2-secret")
    finally:
        analytics_common.reset_secrets()


def test_the_dry_run_resolves_the_path_without_connecting(monkeypatch, capsys):
    def no_connections(*_args, **_kwargs):
        raise AssertionError("--dry-run must not open a connection")

    monkeypatch.setattr(pub, "connect", no_connections)
    for name, value in (("REPORTS_SFTP_HOST", "ftp.example.com"),
                        ("REPORTS_SFTP_USER", "reports"),
                        ("REPORTS_SFTP_PASS", "pw"),
                        ("REPORTS_BASE_PATH", BASE)):
        monkeypatch.setenv(name, value)

    assert pub.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert EXPECTED_DIR in out
    assert f"{EXPECTED_DIR}/index.html" in out
    assert "nothing was uploaded" in out


# --------------------------------------------------------------------------
# Nothing leaks into the repository or the Clarity budget
# --------------------------------------------------------------------------

def test_generating_the_dashboard_makes_no_clarity_api_call(healthy):
    # The autouse fixture turns any Clarity call into a failure.
    assert dash.render_dashboard(healthy)


def test_the_dashboard_is_not_written_into_the_repository(tmp_path):
    before = set(Path(".").glob("**/index.html"))
    dash.main(["--fixture", "low_volume", "--out", str(tmp_path / "index.html")])
    assert set(Path(".").glob("**/index.html")) == before


def test_the_schema_version_is_stated_on_the_page(healthy):
    assert rs.SCHEMA_VERSION in dash.render_dashboard(healthy)


# --------------------------------------------------------------------------
# Diagnosing an unreachable host without disclosing it
# --------------------------------------------------------------------------

def test_a_url_pasted_as_a_hostname_is_named_as_the_problem():
    notes = " ".join(pub.describe_host_shape("ftps://ftp.example.com/reports"))
    assert "bare hostname" in notes
    assert "no path" in notes


def test_an_embedded_port_is_named():
    assert any("port" in n for n in pub.describe_host_shape("ftp.example.com:21"))


def test_a_bare_label_is_named():
    assert any("no dot" in n for n in pub.describe_host_shape("reportserver"))


def test_a_well_shaped_hostname_points_at_dns_or_the_name_itself():
    notes = " ".join(pub.describe_host_shape("ftp.example.com"))
    assert "looks like a hostname" in notes


def test_the_diagnosis_never_repeats_the_hostname():
    """It is a masked secret; the whole point is to describe, not disclose."""
    secret = "ftps://verysecrethost.example.com:21/path"
    for note in pub.describe_host_shape(secret):
        assert "verysecrethost" not in note
        assert secret not in note


def test_an_ip_address_is_recognised_as_such():
    assert pub._looks_like_ip("72.167.124.157")
    assert pub._looks_like_ip("2001:db8::1")
    assert not pub._looks_like_ip("ftp.example.com")


def test_an_ip_that_fails_to_resolve_is_diagnosed_as_a_delivery_problem():
    """An IP needs no DNS, so 'could not resolve' means the value in the
    runner is not the value that was set."""
    notes = " ".join(pub.describe_host_shape("72.167.124.157"))
    assert "needs no DNS" in notes
    assert "looks like a hostname" not in notes


def test_tls_failures_are_not_reported_as_dns_failures(monkeypatch, capsys, tmp_path):
    """A certificate problem and a resolver problem need different answers."""
    import ssl as ssl_module

    page = tmp_path / "index.html"
    page.write_text("<!doctype html>", encoding="utf-8")

    def failing_tls(*_args, **_kwargs):
        raise ssl_module.SSLError("certificate verify failed: IP address mismatch")

    monkeypatch.setattr(pub, "connect", failing_tls)
    monkeypatch.setattr(pub, "certificate_names", lambda *_a, **_k: None)
    for name, value in (("REPORTS_SFTP_HOST", "72.167.124.157"),
                        ("REPORTS_SFTP_USER", "u"), ("REPORTS_SFTP_PASS", "p"),
                        ("REPORTS_BASE_PATH", BASE)):
        monkeypatch.setenv(name, value)

    assert pub.main(["--file", str(page)]) == 1
    err = capsys.readouterr().err
    assert "TLS handshake" in err
    assert "certificate hostname verification cannot succeed" in err
    assert "could not resolve" not in err


def test_a_refused_connection_is_not_reported_as_a_dns_failure(monkeypatch, capsys, tmp_path):
    page = tmp_path / "index.html"
    page.write_text("<!doctype html>", encoding="utf-8")

    def refused(*_args, **_kwargs):
        raise ConnectionRefusedError(111, "Connection refused")

    monkeypatch.setattr(pub, "connect", refused)
    for name, value in (("REPORTS_SFTP_HOST", "ftp.example.com"),
                        ("REPORTS_SFTP_USER", "u"), ("REPORTS_SFTP_PASS", "p"),
                        ("REPORTS_BASE_PATH", BASE)):
        monkeypatch.setenv(name, value)

    assert pub.main(["--file", str(page)]) == 1
    err = capsys.readouterr().err
    assert "could not connect" in err
    assert "may be closed, filtered" in err
    assert "could not resolve" not in err


# --------------------------------------------------------------------------
# Reading the certificate's names to make the fix a single step
# --------------------------------------------------------------------------

def test_certificate_names_are_collected_from_san_and_common_name(monkeypatch):
    class FakeSock:
        def getpeercert(self):
            return {"subject": ((("commonName", "ftp.example.com"),),),
                    "subjectAltName": (("DNS", "ftp.example.com"),
                                       ("DNS", "*.example.com"),
                                       ("IP Address", "1.2.3.4"))}

    class FakeFTPS:
        sock = FakeSock()

        def __init__(self, *a, **k):
            pass

        def connect(self, *a, **k):
            pass

        def auth(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(pub.ftplib, "FTP_TLS", FakeFTPS)

    assert pub.certificate_names("1.2.3.4") == ["*.example.com", "ftp.example.com"]


def test_reading_the_certificate_never_logs_in_or_uploads():
    """It completes the handshake and hangs up. Credentials and data only ever
    go over the fully verified connection in connect()."""
    import inspect

    body = inspect.getsource(pub.certificate_names)
    body = body.split('"""')[2]        # drop the docstring; scan the code only
    for forbidden in ("login", "storbinary", "prot_p", "password"):
        assert forbidden not in body, forbidden


def test_the_certificate_probe_still_validates_the_chain():
    """check_hostname is off — that is the question being asked. verify_mode
    must stay on, or this would be trusting any certificate at all."""
    import inspect

    body = inspect.getsource(pub.certificate_names).split('"""')[2]
    assert "check_hostname = False" in body
    assert "CERT_NONE" not in body
    assert "verify_mode" not in body


def test_a_failed_probe_returns_none_rather_than_raising(monkeypatch):
    class Exploding:
        def __init__(self, *a, **k):
            pass

        def connect(self, *a, **k):
            raise OSError("unreachable")

        def close(self):
            pass

    monkeypatch.setattr(pub.ftplib, "FTP_TLS", Exploding)
    assert pub.certificate_names("nowhere.invalid") is None


def test_a_tls_failure_reports_the_certificate_names(monkeypatch, capsys, tmp_path):
    page = tmp_path / "index.html"
    page.write_text("<!doctype html>", encoding="utf-8")

    def failing_tls(*_args, **_kwargs):
        raise ssl.SSLError("certificate verify failed: Hostname mismatch")

    monkeypatch.setattr(pub, "connect", failing_tls)
    monkeypatch.setattr(pub, "certificate_names",
                        lambda *_a, **_k: ["ftp.realname.com", "realname.com"])
    for name, value in (("REPORTS_SFTP_HOST", "ftp.wrongname.com"),
                        ("REPORTS_SFTP_USER", "u"), ("REPORTS_SFTP_PASS", "p"),
                        ("REPORTS_BASE_PATH", BASE)):
        monkeypatch.setenv(name, value)

    assert pub.main(["--file", str(page)]) == 1
    err = capsys.readouterr().err
    assert "valid for:" in err
    assert "ftp.realname.com" in err
    assert "no credentials were sent" in err.replace("\n", " ").replace("  ", " ")


# --------------------------------------------------------------------------
# Naming the hostname that satisfies BOTH halves
# --------------------------------------------------------------------------

def _report(monkeypatch, cert_names, dns, host="72.167.124.157"):
    import io

    monkeypatch.setattr(pub, "certificate_names", lambda *_a, **_k: cert_names)
    monkeypatch.setattr(pub, "resolve", lambda name: dns.get(name, []))
    buffer = io.StringIO()
    answer = pub.certificate_report(host, out=buffer)
    return answer, buffer.getvalue()


def test_the_report_names_the_hostname_that_resolves_to_this_server(monkeypatch):
    answer, text = _report(
        monkeypatch,
        ["ftp.example.com", "mail.example.com"],
        {"ftp.example.com": ["72.167.124.157"], "mail.example.com": ["9.9.9.9"]})

    assert answer == "ftp.example.com"
    assert "ANSWER: set REPORTS_SFTP_HOST to  ftp.example.com" in text
    assert "MATCHES this server" in text
    assert "different server" in text


def test_a_certificate_name_that_does_not_resolve_is_called_out(monkeypatch):
    answer, text = _report(monkeypatch, ["ftp.example.com"], {})

    assert answer is None
    assert "does NOT resolve" in text
    assert "none of the certificate's names currently resolves" in text


def test_a_name_pointing_elsewhere_is_not_offered_as_the_answer(monkeypatch):
    answer, text = _report(monkeypatch, ["ftp.other.com"],
                           {"ftp.other.com": ["203.0.113.9"]})

    assert answer is None
    assert "different server" in text


def test_a_wildcard_certificate_is_reported_as_the_easy_fix(monkeypatch):
    answer, text = _report(monkeypatch, ["*.example.com"], {})

    assert answer is None
    assert "covers *.example.com" in text
    assert "pointing one at this server in DNS is the fix" in text


def test_the_shortest_matching_name_is_preferred(monkeypatch):
    answer, _text = _report(
        monkeypatch,
        ["a.very.long.name.example.com", "ftp.example.com"],
        {"a.very.long.name.example.com": ["72.167.124.157"],
         "ftp.example.com": ["72.167.124.157"]})

    assert answer == "ftp.example.com"


def test_an_unreadable_certificate_says_so_rather_than_guessing(monkeypatch):
    answer, text = _report(monkeypatch, None, {})

    assert answer is None
    assert "could not be read" in text


def test_the_report_reads_no_secrets_and_uploads_nothing(monkeypatch, capsys):
    """It runs before load_settings(), so it works with no credentials at all."""
    monkeypatch.delenv("REPORTS_SFTP_HOST", raising=False)
    monkeypatch.delenv("REPORTS_SFTP_PASS", raising=False)
    monkeypatch.setattr(pub, "certificate_report", lambda *_a, **_k: None)

    assert pub.main(["--certificate-report", "72.167.124.157"]) == 0


def test_resolve_returns_empty_for_an_unresolvable_name():
    assert pub.resolve("no-such-host.invalid") == []
