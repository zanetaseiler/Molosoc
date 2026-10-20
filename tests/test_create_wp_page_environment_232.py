"""Issue #232: create_wp_page.py must refuse a WP_URL that doesn't match --environment."""
import importlib.util
import os
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automations/content-sync/create_wp_page.py"
WF = (ROOT / ".github/workflows/create-wp-page.yml").read_text(encoding="utf-8")


def load(wp_url):
    env = {"WP_URL": wp_url, "WP_USER": "u", "WP_APP_PASSWORD": "p"}
    with mock.patch.dict(os.environ, env):
        spec = importlib.util.spec_from_file_location("create_wp_page", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod


class EnvironmentSelection(unittest.TestCase):
    def test_matching_hosts_accepted(self):
        m = load("https://molosoc.com/")
        m.validate_wp_url("https://molosoc.com", "production")
        m.validate_wp_url("https://staging.molosoc.com", "staging")

    def test_mismatches_refused(self):
        m = load("https://molosoc.com")
        for url, env in [
            ("https://staging.molosoc.com", "production"),
            ("https://molosoc.com", "staging"),
            ("http://molosoc.com", "production"),
            ("https://molosoc.com.evil.test", "production"),
            ("https://user:pw@molosoc.com", "production"),
            ("https://molosoc.com:8443", "production"),
            ("", "production"),
        ]:
            with self.subTest(url=url, env=env), self.assertRaises(SystemExit):
                m.validate_wp_url(url, env)

    def test_mismatch_refused_before_any_request(self):
        m = load("https://staging.molosoc.com")
        argv = ["x", "--environment", "production", "--slug", "s", "--title", "t"]
        with mock.patch("sys.argv", argv), mock.patch.object(m.requests, "get") as g, \
                mock.patch.object(m.requests, "post") as p, self.assertRaises(SystemExit):
            m.main()
        g.assert_not_called()
        p.assert_not_called()

    def test_environment_required(self):
        m = load("https://molosoc.com")
        with mock.patch("sys.argv", ["x", "--slug", "s", "--title", "t"]), self.assertRaises(SystemExit):
            m.main()

    def test_workflow_selects_secrets_per_environment_and_stays_draft(self):
        self.assertIn("type: choice", WF)
        self.assertIn("- production", WF)
        self.assertIn("- staging", WF)
        self.assertIn("secrets.PROD_WP_URL", WF)
        self.assertIn("secrets.PROD_WP_USER", WF)
        self.assertIn("secrets.PROD_WP_APP_PASSWORD", WF)
        self.assertIn('--environment "${{ inputs.environment }}"', WF)
        self.assertIn("--lang", WF)
        self.assertIn('"status": "draft"', SCRIPT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
