"""Issue #205: production theme deploys must purge WP-Optimize's page cache.

Static checks on .github/workflows/production.yml (no network, no deploy).
"""
import re
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/production.yml"


class PostDeployCachePurgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = WORKFLOW.read_text(encoding="utf-8")
        match = re.search(r"\n  purge-page-cache:\n(.*)\Z", cls.src, re.S)
        assert match, "purge-page-cache job not found"
        cls.job = match.group(1)
        cls.code = "\n".join(
            l for l in cls.job.splitlines() if not l.lstrip().startswith("#")
        )
        cls.deploy = cls.src[: match.start()]

    def test_runs_only_after_successful_deploy(self):
        self.assertIn("needs: deploy", self.job)
        self.assertIn("if: success()", self.job)

    def test_deploy_job_unchanged_and_triggers_intact(self):
        self.assertIn('branches: [main]', self.deploy)
        self.assertIn('- "site/theme/**"', self.deploy)
        self.assertIn("SamKirkland/FTP-Deploy-Action@v4.4.0", self.deploy)
        self.assertIn("server-dir: /wp-content/themes/molosoc/", self.deploy)

    def test_only_existing_secrets_no_hardcoded_credentials(self):
        secrets = set(re.findall(r"secrets\.(\w+)", self.job))
        self.assertEqual(secrets, {"PROD_SFTP_HOST", "PROD_SFTP_USER", "PROD_SFTP_PASS"})

    def test_single_exact_cache_path_no_wildcards(self):
        self.assertEqual(re.findall(r"rm -rf (\S+);", self.job), ["$CACHE_DIR"])
        self.assertIn("CACHE_DIR=/wp-content/cache/wpo-cache", self.job)
        for forbidden in ("woocommerce", "uploads", "wp-admin", "wp-json", "ssh ", "mirror"):
            self.assertNotIn(forbidden, self.code)
        self.assertNotRegex(self.code, r"rm -rf \S*[*?]")

    def test_failures_are_visible(self):
        self.assertIn("set -eu", self.job)
        self.assertNotIn("|| true", self.code)
        self.assertIn("exit 1", self.job)
        self.assertIn("secrets missing", self.job)
        self.assertNotIn("still present after purge", self.job)
        self.assertIn("recreated by a fresh request", self.job)

    def test_idempotent_when_cache_absent(self):
        self.assertIn("already absent", self.job)

    def test_tls_verification_not_disabled(self):
        self.assertNotIn("verify-certificate no", self.job)


if __name__ == "__main__":
    unittest.main()
