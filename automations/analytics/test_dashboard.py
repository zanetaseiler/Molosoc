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
import io
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
KEY = "-----BEGIN OPENSSH PRIVATE KEY-----\nnotarealkey\n-----END OPENSSH PRIVATE KEY-----\n"


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

    assert page.startswith("<!DOCTYPE html>")
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

    for heading in ("Weekly Analytics", "Traffic", "Search",
                    "Behaviour", "Ecommerce and conversions",
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
    assert page.count('class="td-priority ') == len(healthy["recommendations"])


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
    assert "More evidence needed" in page
    # Case-insensitive: the note is the producer's own clause, capitalised for
    # display so it does not open the report looking like an error string.
    assert "insufficient data" in page.lower()


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
    assert 'id="trends"' in page and "td-sparkline" in page
    assert "<svg" in page and "polyline" in page
    assert "6 weekly reports" in page


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def test_the_cli_writes_a_file_from_a_fixture(tmp_path):
    out = tmp_path / "index.html"
    assert dash.main(["--fixture", "low_volume", "--out", str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_the_cli_renders_a_stored_report_document(tmp_path, healthy):
    import json

    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(healthy), encoding="utf-8")
    out = tmp_path / "index.html"

    assert dash.main(["--report", str(report_path), "--out", str(out)]) == 0
    assert "Weekly Analytics" in out.read_text(encoding="utf-8")


def test_a_missing_index_costs_the_trend_strip_not_the_page(tmp_path):
    out = tmp_path / "index.html"
    code = dash.main(["--fixture", "healthy", "--out", str(out),
                      "--index", str(tmp_path / "nope.json")])
    assert code == 0
    assert "Weekly Analytics" in out.read_text(encoding="utf-8")


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
#
# These guards are transport-independent and survived the move from FTPS to
# SFTP unchanged, which is the point of deriving the path rather than passing
# it in: swapping the protocol could not move where the file lands.
# --------------------------------------------------------------------------

def test_the_remote_directory_is_the_molosoc_folder_under_the_base_path():
    assert pub.resolve_remote_dir(BASE) == EXPECTED_DIR
    assert pub.resolve_remote_dir(BASE + "/") == EXPECTED_DIR


def test_an_unset_base_path_falls_back_to_the_committed_default():
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
# Settings: one new secret, everything else derived or reused
# --------------------------------------------------------------------------

def test_the_ssh_user_falls_back_to_the_existing_reports_user():
    """The move to SFTP was meant to need exactly one new secret."""
    settings = pub.load_settings({"REPORTS_SFTP_USER": "cpaneluser",
                                  "REPORTS_SSH_KEY": KEY})
    assert settings["user"] == "cpaneluser"
    assert settings["user_source"] == "REPORTS_SFTP_USER"


def test_an_explicit_ssh_user_wins():
    settings = pub.load_settings({"REPORTS_SFTP_USER": "ftponly",
                                  "REPORTS_SSH_USER": "sshuser",
                                  "REPORTS_SSH_KEY": KEY})
    assert settings["user"] == "sshuser"
    assert settings["user_source"] == "REPORTS_SSH_USER"


def test_the_host_defaults_to_the_cpanel_server():
    settings = pub.load_settings({"REPORTS_SFTP_USER": "u", "REPORTS_SSH_KEY": KEY})
    assert settings["host"] == "p3plmcpnl502709.prod.phx3.secureserver.net"
    assert pub.SSH_PORT == 22


def test_a_missing_key_is_the_one_thing_that_stops_the_run():
    with pytest.raises(pub.PublishError, match="REPORTS_SSH_KEY"):
        pub.load_settings({"REPORTS_SFTP_USER": "u"})


def test_a_missing_user_names_both_secrets_that_could_supply_it():
    with pytest.raises(pub.PublishError) as excinfo:
        pub.load_settings({"REPORTS_SSH_KEY": KEY})
    assert "REPORTS_SSH_USER" in str(excinfo.value)
    assert "REPORTS_SFTP_USER" in str(excinfo.value)


def test_the_private_key_is_registered_for_redaction():
    import analytics_common

    analytics_common.reset_secrets()
    try:
        pub.load_settings({"REPORTS_SFTP_USER": "u", "REPORTS_SSH_KEY": KEY})
        assert KEY not in analytics_common.redact(f"auth failed using {KEY}")
    finally:
        analytics_common.reset_secrets()


# --------------------------------------------------------------------------
# The private key
# --------------------------------------------------------------------------

def test_a_key_that_is_not_a_key_says_so_plainly():
    with pytest.raises(pub.PublishError, match="does not contain a private key"):
        pub.load_private_key("hunter2")


def test_a_base64_wrapped_key_is_unwrapped_before_parsing():
    """A multi-line secret pasted into a single-line field is the classic
    mistake; failing with 'could not parse' would send someone the wrong way."""
    import base64 as b64

    wrapped = b64.b64encode(KEY.encode()).decode()
    with pytest.raises(pub.PublishError) as excinfo:
        pub.load_private_key(wrapped)
    # It got past the "not a key" check and into real parsing.
    assert "does not contain a private key" not in str(excinfo.value)
    assert "could not be parsed" in str(excinfo.value)


def test_an_unparseable_key_mentions_the_passphrase_case():
    with pytest.raises(pub.PublishError, match="passphrase"):
        pub.load_private_key(KEY)


def test_a_real_key_round_trips():
    import paramiko

    generated = paramiko.Ed25519Key.generate() if hasattr(paramiko.Ed25519Key, "generate") \
        else paramiko.RSAKey.generate(2048)
    buffer = io.StringIO()
    generated.write_private_key(buffer)

    parsed = pub.load_private_key(buffer.getvalue())
    assert parsed.get_base64() == generated.get_base64()


def test_the_host_key_fingerprint_is_the_sha256_form():
    import base64 as b64
    import hashlib

    class FakeKey:
        def asbytes(self):
            return b"host-key-bytes"

    expected = "SHA256:" + b64.b64encode(
        hashlib.sha256(b"host-key-bytes").digest()).decode().rstrip("=")
    assert pub.fingerprint(FakeKey()) == expected


def test_the_public_half_is_reported_in_the_form_cpanel_shows():
    import paramiko

    generated = paramiko.Ed25519Key.generate() if hasattr(paramiko.Ed25519Key, "generate") \
        else paramiko.RSAKey.generate(2048)
    line, digest = pub.describe_public_key(generated)

    # A known_hosts/authorized_keys line, so it can be pasted into cPanel,
    # and the same fingerprint form cPanel and ssh-keygen -l both print.
    assert line == f"{generated.get_name()} {generated.get_base64()}"
    assert digest == pub.fingerprint(generated)


def test_the_public_half_never_carries_the_private_half():
    import paramiko

    generated = paramiko.Ed25519Key.generate() if hasattr(paramiko.Ed25519Key, "generate") \
        else paramiko.RSAKey.generate(2048)
    buffer = io.StringIO()
    generated.write_private_key(buffer)
    secret = buffer.getvalue()

    line, digest = pub.describe_public_key(generated)
    for private_line in secret.splitlines():
        if "PRIVATE KEY" in private_line or not private_line.strip():
            continue
        assert private_line not in line
        assert private_line not in digest


def test_an_ftp_subaccount_username_is_named_as_the_likely_cause():
    notes = " ".join(pub.describe_user_shape("reports@trafficdom.com"))
    assert "FTP sub-account" in notes
    assert "REPORTS_SSH_USER" in notes


def test_a_plain_cpanel_username_draws_no_complaint():
    assert pub.describe_user_shape("molosoc") == []


def test_the_username_is_never_printed_by_its_own_diagnosis():
    for user in ("reports@trafficdom.com", "molosoc ", "with space"):
        for note in pub.describe_user_shape(user):
            assert user not in note
            assert user.strip() not in note


# --------------------------------------------------------------------------
# The server's own working directory is what decides
# --------------------------------------------------------------------------

class FakeSFTP:
    """Enough of paramiko.SFTPClient to drive the guards."""

    def __init__(self, cwd="/", dirs=()):
        self._cwd = cwd
        self._dirs = set(dirs)
        self.stored = []
        self.made = []

    def chdir(self, path):
        target = path if path.startswith("/") else f"{self._cwd.rstrip('/')}/{path}"
        if target not in self._dirs:
            raise IOError(f"No such file: {target}")
        self._cwd = target

    def getcwd(self):
        return self._cwd

    def mkdir(self, name):
        target = f"{self._cwd.rstrip('/')}/{name}"
        self._dirs.add(target)
        self.made.append(target)

    def put(self, local_path, remote_name):
        with open(local_path, "rb") as handle:
            self.stored.append((remote_name, self._cwd, handle.read()))

    def stat(self, name):
        class Attrs:
            st_mode = 0o100644
            st_size = len(self.stored[-1][2]) if self.stored else 0
        return Attrs()


def test_the_upload_is_abandoned_when_the_server_reports_a_different_directory():
    """A chroot or a symlink can land a locally-correct path elsewhere."""
    sftp = FakeSFTP(cwd="/public_html/someone-elses-site")

    with pytest.raises(pub.PublishError) as excinfo:
        pub.verify_location(sftp, EXPECTED_DIR)

    assert "FAILED" in str(excinfo.value)
    assert "Nothing was uploaded" in str(excinfo.value)
    assert not sftp.stored


def test_the_location_check_passes_on_the_expected_directory():
    assert pub.verify_location(FakeSFTP(cwd=EXPECTED_DIR), EXPECTED_DIR) == EXPECTED_DIR


def test_a_chrooted_account_reporting_a_shorter_path_still_verifies():
    sftp = FakeSFTP(cwd="/reports/molosoc")
    assert pub.verify_location(sftp, EXPECTED_DIR) == "/reports/molosoc"


def test_a_sibling_project_directory_is_rejected():
    sftp = FakeSFTP(cwd="/public_html/Trafficdom.com/reports/othersite")
    with pytest.raises(pub.PublishError):
        pub.verify_location(sftp, EXPECTED_DIR)


def test_a_missing_base_path_is_an_error_rather_than_a_directory_to_invent():
    sftp = FakeSFTP(cwd="/", dirs={"/"})

    with pytest.raises(pub.PublishError, match="does not exist or is not reachable"):
        pub.enter_remote_dir(sftp, EXPECTED_DIR)
    assert not sftp.made


def test_only_the_project_directory_is_ever_created():
    sftp = FakeSFTP(cwd="/", dirs={"/", BASE})

    assert pub.enter_remote_dir(sftp, EXPECTED_DIR) == EXPECTED_DIR
    assert sftp.made == [EXPECTED_DIR], "nothing above the project dir may be created"


def test_an_existing_project_directory_is_entered_without_being_recreated():
    sftp = FakeSFTP(cwd="/", dirs={"/", BASE, EXPECTED_DIR})
    assert pub.enter_remote_dir(sftp, EXPECTED_DIR) == EXPECTED_DIR
    assert sftp.made == []


HOME = "/home/lf7mcmvh2g6m"
HOME_DIR = HOME + EXPECTED_DIR


def test_the_base_path_is_found_inside_the_home_directory_when_not_at_the_root():
    """What FTP calls /public_html/... is $HOME/public_html/... over SSH."""
    sftp = FakeSFTP(cwd=HOME, dirs={"/", HOME, HOME + BASE})

    assert pub.enter_remote_dir(sftp, EXPECTED_DIR, home=HOME) == HOME_DIR
    assert sftp.made == [HOME_DIR], "only the project directory may be created"


def test_the_literal_path_wins_when_it_exists():
    """The fallback must never redirect a path that already resolves."""
    sftp = FakeSFTP(cwd="/", dirs={"/", BASE, HOME, HOME + BASE})

    assert pub.enter_remote_dir(sftp, EXPECTED_DIR, home=HOME) == EXPECTED_DIR


def test_the_home_fallback_still_lands_on_the_molosoc_folder():
    sftp = FakeSFTP(cwd=HOME, dirs={"/", HOME, HOME + BASE})
    pub.enter_remote_dir(sftp, EXPECTED_DIR, home=HOME)

    # The server's own answer is what the location check is given, and the
    # home-prefixed path must still satisfy it.
    assert pub.verify_location(sftp, EXPECTED_DIR) == HOME_DIR


def test_neither_path_existing_is_still_an_error_rather_than_a_tree_to_build():
    sftp = FakeSFTP(cwd="/", dirs={"/", HOME})

    with pytest.raises(pub.PublishError, match="does not exist or is not reachable"):
        pub.enter_remote_dir(sftp, EXPECTED_DIR, home=HOME)
    assert not sftp.made


def test_the_home_fallback_obeys_the_same_rules_as_the_derived_path():
    with pytest.raises(pub.PublishError, match="WordPress"):
        pub.home_relative(EXPECTED_DIR, "/home/user/wp-content")
    with pytest.raises(pub.PublishError, match="relative segments"):
        pub.home_relative(EXPECTED_DIR, "/home/..")


def test_a_useless_home_gives_nothing_to_fall_back_to():
    assert pub.home_relative(EXPECTED_DIR, "/") is None
    assert pub.home_relative(EXPECTED_DIR, "") is None
    assert pub.home_relative(EXPECTED_DIR, "relative/path") is None
    # Already inside the home directory — there is nothing to prefix.
    assert pub.home_relative(HOME_DIR, HOME) is None


def test_the_upload_stores_exactly_one_file_in_the_verified_directory(tmp_path):
    page = tmp_path / "index.html"
    page.write_text("<!doctype html><html></html>", encoding="utf-8")
    sftp = FakeSFTP(cwd="/", dirs={"/", BASE, EXPECTED_DIR})
    pub.enter_remote_dir(sftp, EXPECTED_DIR)
    pub.verify_location(sftp, EXPECTED_DIR)

    sent = pub.upload(sftp, str(page))

    assert len(sftp.stored) == 1
    name, cwd, _body = sftp.stored[0]
    assert name == "index.html"
    assert cwd == EXPECTED_DIR
    assert pub.confirm_uploaded(sftp, sent) == (sent, None)


def test_a_size_mismatch_is_reported_rather_than_passed_over(tmp_path):
    page = tmp_path / "index.html"
    page.write_text("<!doctype html>", encoding="utf-8")
    sftp = FakeSFTP(cwd="/", dirs={"/", BASE, EXPECTED_DIR})
    pub.enter_remote_dir(sftp, EXPECTED_DIR)
    pub.upload(sftp, str(page))

    _size, problem = pub.confirm_uploaded(sftp, 999999)
    assert "size mismatch" in problem


def test_the_publisher_never_deletes_or_renames():
    source = Path(pub.__file__).read_text(encoding="utf-8")
    for destructive in (".remove(", ".unlink(", ".rmdir(", ".rename(", ".rmtree("):
        assert destructive not in source, destructive


def test_ftps_is_gone_entirely():
    """The shared host's certificate could never verify, so the transport was
    replaced rather than its verification weakened."""
    source = Path(pub.__file__).read_text(encoding="utf-8")
    assert "ftplib" not in source
    assert "FTP_TLS" not in source
    assert "check_hostname" not in source
    assert "CERT_NONE" not in source
    assert "verify_mode" not in source


def test_the_dry_run_resolves_the_path_without_connecting(monkeypatch, capsys):
    def no_connections(*_args, **_kwargs):
        raise AssertionError("--dry-run must not open a connection")

    monkeypatch.setattr(pub, "connect", no_connections)
    for name, value in (("REPORTS_SFTP_USER", "reports"), ("REPORTS_SSH_KEY", KEY),
                        ("REPORTS_BASE_PATH", BASE)):
        monkeypatch.setenv(name, value)

    assert pub.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert EXPECTED_DIR in out
    assert f"{EXPECTED_DIR}/index.html" in out
    assert "port 22" in out or ":22" in out
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
