"""
The authenticated verification of a password-protected report.

These tests run the real script against a real HTTP server with a real Basic
Auth realm. Nothing is mocked and nothing pattern-matches the YAML, because the
thing that can be wrong here is what the shell and curl actually do — a check
that passes when it should fail is the whole failure mode this file exists to
prevent.
"""

import base64
import hashlib
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("verify_published_report.sh")

USER = "molosoc-reports"
PASSWORD = "s3cret-do-not-log"          # noqa: S105 - fixture, not a real one
REALM = "Protected 'public_html/Trafficdom.com/reports/molosoc'"

PAGE = (b"<!doctype html><html><head><title>Email Marketing Report</title>"
        b"</head><body><div class='td-wrap'>Email Marketing Report</div>"
        b"</body></html>")
PAGE_SHA = hashlib.sha256(PAGE).hexdigest()


class Handler(BaseHTTPRequestHandler):
    """Serves one page, and only to a caller that authenticates."""

    def log_message(self, *args):        # keep pytest output readable
        pass

    def do_GET(self):
        expected = base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()
        supplied = self.headers.get("Authorization", "")
        if supplied != f"Basic {expected}":
            body = b"Unauthorized\n"
            self.send_response(401)
            self.send_header("WWW-Authenticate", f'Basic realm="{REALM}"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path.startswith("/wrong-page"):
            body = b"<html><title>Some other page</title></html>"
        else:
            body = PAGE
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


@pytest.fixture(scope="module")
def base_url():
    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


def run(tmp_path, **overrides):
    env = dict(os.environ)
    env.pop("VERIFY_EXPECT_SHA256", None)
    env["RUNNER_TEMP"] = str(tmp_path)
    for key, value in overrides.items():
        name = f"VERIFY_{key.upper()}"
        if value is None:
            env.pop(name, None)
        else:
            env[name] = value
    return subprocess.run(["bash", str(SCRIPT)], env=env,
                          capture_output=True, text=True)


def good(base_url, **overrides):
    settings = {"url": f"{base_url}/reports/molosoc/email-marketing/",
                "marker": "Email Marketing Report",
                "user": USER, "password": PASSWORD}
    settings.update(overrides)
    return settings


class TestItPassesOnlyWhenEverythingHolds:

    def test_correct_credentials_marker_and_hash(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url, expect_sha256=PAGE_SHA))
        assert done.returncode == 0, done.stderr
        assert "PASS" in done.stdout
        assert "byte-identical" in done.stdout

    def test_the_hash_is_optional(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url))
        assert done.returncode == 0, done.stderr
        assert "byte-identical" not in done.stdout

    def test_the_marker_is_case_insensitive(self, base_url, tmp_path):
        """A title-case change has broken this check before."""
        done = run(tmp_path, **good(base_url, marker="EMAIL MARKETING report"))
        assert done.returncode == 0, done.stderr


class TestAFourZeroOneIsAlwaysAFailure:

    def test_wrong_password_fails(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url, password="not-the-password"))
        assert done.returncode == 1
        assert "401" in done.stderr
        assert "rejected these credentials" in done.stderr

    def test_wrong_user_fails(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url, user="somebody-else"))
        assert done.returncode == 1
        assert "401" in done.stderr

    def test_the_message_does_not_suggest_removing_the_protection(
            self, base_url, tmp_path):
        """The realm is intentional. The log must not imply otherwise."""
        done = run(tmp_path, **good(base_url, password="wrong"))
        assert "Basic Auth stays enabled" in done.stderr


class TestAMissingSecretIsNotAServingFailure:
    """Exit 2, not 1 — and never a 401 message.

    An unset secret and a wrong password are indistinguishable on the wire.
    Reporting the first as the second sends someone to cPanel to debug a
    GitHub setting, which is the most expensive wrong turn available here.
    """

    def test_no_user_is_a_configuration_error(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url, user=""))
        assert done.returncode == 2
        assert "not configured" in done.stderr
        assert "401" not in done.stderr

    def test_no_password_is_a_configuration_error(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url, password=""))
        assert done.returncode == 2
        assert "not configured" in done.stderr

    def test_an_unset_variable_behaves_like_an_empty_one(self, base_url,
                                                         tmp_path):
        done = run(tmp_path, **good(base_url, password=None))
        assert done.returncode == 2

    def test_it_says_nothing_was_verified(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url, user=""))
        assert "Nothing was verified" in done.stderr

    def test_a_missing_url_is_also_a_configuration_error(self, tmp_path):
        done = run(tmp_path, url="", user=USER, password=PASSWORD)
        assert done.returncode == 2


class TestAuthenticatedButWrong:

    def test_a_page_without_the_marker_fails(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url,
                                    url=f"{base_url}/wrong-page"))
        assert done.returncode == 1
        assert "not this report" in done.stderr

    def test_a_hash_mismatch_fails(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url, expect_sha256="0" * 64))
        assert done.returncode == 1
        assert "not the bytes published" in done.stderr

    def test_the_hash_mismatch_names_both_hashes(self, base_url, tmp_path):
        done = run(tmp_path, **good(base_url, expect_sha256="0" * 64))
        assert PAGE_SHA in done.stderr

    def test_an_unreachable_host_fails_rather_than_passes(self, tmp_path):
        done = run(tmp_path, url="http://127.0.0.1:9/nothing",
                   marker="anything", user=USER, password=PASSWORD)
        assert done.returncode == 1


class TestTheCredentialNeverEscapes:

    def test_it_appears_in_neither_output_stream(self, base_url, tmp_path):
        for settings in (good(base_url),
                         good(base_url, password="wrong-" + PASSWORD),
                         good(base_url, expect_sha256="0" * 64)):
            done = run(tmp_path, **settings)
            assert PASSWORD not in done.stdout
            assert PASSWORD not in done.stderr
            assert settings["password"] not in done.stdout
            assert settings["password"] not in done.stderr

    def test_the_curl_config_is_removed_even_when_the_check_fails(
            self, base_url, tmp_path):
        run(tmp_path, **good(base_url, password="wrong"))
        assert list(tmp_path.glob("curlrc*")) == []
        assert list(tmp_path.glob("body*")) == []

    def test_no_credential_is_left_behind_on_success(self, base_url, tmp_path):
        run(tmp_path, **good(base_url))
        leftovers = [p for p in tmp_path.iterdir() if p.is_file()]
        assert leftovers == []

    def test_the_script_never_passes_a_credential_on_a_command_line(self):
        """`ps` can read argv; a mode-600 config file it cannot."""
        text = SCRIPT.read_text(encoding="utf-8")
        body = "\n".join(line for line in text.splitlines()
                         if not line.lstrip().startswith("#"))
        assert "curl -u" not in body
        assert "--user" not in body
        assert "--config" in body

    def test_it_does_not_replay_credentials_across_hosts(self):
        text = SCRIPT.read_text(encoding="utf-8")
        body = "\n".join(line for line in text.splitlines()
                         if not line.lstrip().startswith("#"))
        assert "--location-trusted" not in body


class TestNoUnauthenticatedCheckSurvivesAnywhere:
    """The regression that would quietly undo all of this.

    Someone adds a verification step, copies the old six-line curl idiom, and
    it 401s forever — or worse, warns and continues. These tests read every
    workflow and refuse both shapes for the protected directory.
    """

    WORKFLOWS = Path(__file__).parents[2] / ".github" / "workflows"
    PROTECTED = "https://trafficdom.com/reports/molosoc"

    def _uncommented(self, path):
        return "\n".join(line for line in
                         path.read_text(encoding="utf-8").splitlines()
                         if not line.lstrip().startswith("#"))

    def test_every_publisher_verifies_through_the_shared_action(self):
        for name in ("publish-email-report.yml", "publish-growth-report.yml",
                     "weekly-marketing-report.yml"):
            body = self._uncommented(self.WORKFLOWS / name)
            assert "./.github/actions/verify-report" in body, name
            assert "REPORT_BASIC_AUTH_USER" in body, name
            assert "REPORT_BASIC_AUTH_PASSWORD" in body, name

    def test_no_publisher_still_curls_the_protected_directory_by_hand(self):
        for name in ("publish-email-report.yml", "publish-growth-report.yml",
                     "weekly-marketing-report.yml"):
            body = self._uncommented(self.WORKFLOWS / name)
            for line in body.splitlines():
                if "curl" in line and self.PROTECTED in line:
                    raise AssertionError(
                        f"{name} still fetches the protected directory by "
                        f"hand: {line.strip()}")

    def test_no_workflow_downgrades_a_failed_report_check_to_a_warning(self):
        """A check that cannot fail reads as a check that passed."""
        for name in ("publish-email-report.yml", "publish-growth-report.yml",
                     "weekly-marketing-report.yml"):
            body = self._uncommented(self.WORKFLOWS / name)
            assert "it may not be published yet" not in body, name

    def test_the_diagnostic_authenticates_but_does_not_assert(self):
        """It must be able to REPORT a 401 rather than exit on one."""
        body = self._uncommented(self.WORKFLOWS / "diagnose-report-serving.yml")
        assert "REPORT_BASIC_AUTH_USER" in body
        assert "./.github/actions/verify-report" not in body

    def test_no_workflow_hard_codes_a_credential(self):
        for path in sorted(self.WORKFLOWS.glob("*.yml")):
            body = self._uncommented(path)
            for line in body.splitlines():
                if "REPORT_BASIC_AUTH" in line and "secrets." not in line:
                    assert "AUTH_USER" in line or "AUTH_PASSWORD" in line, (
                        f"{path.name}: {line.strip()}")

    def test_the_composite_action_takes_credentials_as_inputs(self):
        """Client-agnostic: a second protected folder needs no change here."""
        action = (Path(__file__).parents[2] / ".github" / "actions"
                  / "verify-report" / "action.yml")
        body = self._uncommented(action)
        assert "REPORT_BASIC_AUTH" not in body, (
            "the action must not name a client's secrets; they are inputs")
