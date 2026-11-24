"""Issue #384 — link the Black Friday pages 1128 (CZ) <-> 1129 (EN) in Polylang."""
import importlib.util
import pathlib
import sys
import types
import unittest

try:
    import requests  # noqa: F401
except ImportError:
    sys.modules["requests"] = types.ModuleType("requests")

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automations/content-sync/link_bf_pages.py"
WORKFLOW = ROOT / ".github/workflows/link-bf-pages.yml"
spec = importlib.util.spec_from_file_location("link_bf", SCRIPT)
lb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lb)


class R:
    def __init__(self, status=200, body=None, text=""):
        self.status_code, self._body, self.text = status, body, text

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


SWITCHER_UNLINKED_CZ = (
    '<ul><li class="lang-item lang-item-2 lang-item-cz current-lang lang-item-first">'
    '<a lang="cs-CZ" hreflang="cs-CZ" href="https://molosoc.com/cz/black-friday-molosoc/">CZ</a></li>'
    '<li class="lang-item lang-item-5 lang-item-en no-translation">'
    '<a lang="en-GB" hreflang="en-GB" href="https://molosoc.com/">EN</a></li></ul>'
)


class FakeWP:
    """Minimal fake of the core pages endpoint + molosoc-migrate helper + public pages."""

    def __init__(self, t_cz=None, t_en=None, slug_cz="black-friday-molosoc", helper=True):
        self.t = {1128: dict(t_cz or {"cz": 1128}), 1129: dict(t_en or {"en": 1129})}
        self.slugs = {1128: slug_cz, 1129: "black-friday-offer-molosoc"}
        self.lang = {1128: "cz", 1129: "en"}
        self.helper = helper
        self.posts = []

    def get(self, url, **kw):
        if "/wp/v2/pages/" in url:
            pid = int(url.rsplit("/", 1)[1])
            return R(200, {"id": pid, "slug": self.slugs[pid], "status": "publish", "link": "x"})
        if "/molosoc-migrate/v1/status/" in url:
            if not self.helper:
                return R(404, {"code": "rest_no_route"})
            pid = int(url.rsplit("/", 1)[1])
            return R(200, {"post_id": pid, "language": self.lang[pid], "translations": self.t[pid]})
        return R(200, text=SWITCHER_UNLINKED_CZ)

    def post(self, url, json=None, **kw):
        self.posts.append((url, json))
        tr = json["translations"]
        for pid in tr.values():
            self.t[pid] = dict(tr)
        return R(200, {"saved": tr})


class LinkBf384(unittest.TestCase):
    def run_main(self, wp, *argv):
        orig = (getattr(lb.requests, "get", None), getattr(lb.requests, "post", None), sys.argv)
        lb.requests.get, lb.requests.post = wp.get, wp.post
        sys.argv = ["link_bf_pages.py", *argv]
        env = {"WP_URL": "https://molosoc.com", "WP_USER": "u", "WP_APP_PASSWORD": "p"}
        old_env = {k: lb.os.environ.get(k) for k in env}
        lb.os.environ.update(env)
        try:
            lb.main()
        finally:
            lb.requests.get, lb.requests.post, sys.argv = orig
            for k, v in old_env.items():
                if v is None:
                    lb.os.environ.pop(k, None)
                else:
                    lb.os.environ[k] = v

    def test_fixed_ids_and_slugs(self):
        self.assertEqual(lb.PAGES["cz"], {"id": 1128, "slug": "black-friday-molosoc", "path": "/cz/black-friday-molosoc/"})
        self.assertEqual(lb.PAGES["en"], {"id": 1129, "slug": "black-friday-offer-molosoc", "path": "/black-friday-offer-molosoc/"})

    def test_refuses_wrong_host(self):
        for u in ("https://staging.molosoc.com", "http://molosoc.com", "https://molosoc.com/x", ""):
            with self.assertRaises(SystemExit):
                lb.validate_url(u)
        lb.validate_url("https://molosoc.com")

    def test_dry_run_never_writes(self):
        wp = FakeWP()
        self.run_main(wp)
        self.assertEqual(wp.posts, [])

    def test_apply_links_pair_with_polylang_helper(self):
        wp = FakeWP()
        self.run_main(wp, "--apply")
        self.assertEqual(wp.posts, [("https://molosoc.com/wp-json/molosoc-migrate/v1/link-translations",
                                     {"translations": {"cz": 1128, "en": 1129}})])
        self.assertTrue(lb.is_linked(wp.t[1128], wp.t[1129]))

    def test_apply_is_noop_when_already_linked(self):
        pair = {"cz": 1128, "en": 1129}
        wp = FakeWP(t_cz=pair, t_en=pair)
        self.run_main(wp, "--apply")
        self.assertEqual(wp.posts, [])

    def test_refuses_to_overwrite_another_pairing(self):
        wp = FakeWP(t_en={"en": 1129, "cz": 1065})
        with self.assertRaises(SystemExit) as cm:
            self.run_main(wp, "--apply")
        self.assertIn("1065", str(cm.exception))
        self.assertEqual(wp.posts, [])

    def test_refuses_wrong_page(self):
        wp = FakeWP(slug_cz="something-else")
        with self.assertRaises(SystemExit):
            self.run_main(wp, "--apply")
        self.assertEqual(wp.posts, [])

    def test_missing_helper_aborts_without_write(self):
        wp = FakeWP(helper=False)
        with self.assertRaises(SystemExit) as cm:
            self.run_main(wp, "--apply")
        self.assertIn("wp-admin", str(cm.exception))
        self.assertEqual(wp.posts, [])

    def test_switcher_href_parser(self):
        self.assertEqual(lb.switcher_hrefs(SWITCHER_UNLINKED_CZ),
                         {"cz": "https://molosoc.com/cz/black-friday-molosoc/", "en": "https://molosoc.com/"})
        self.assertEqual(lb.switcher_hrefs(""), {})

    def test_workflow_gated_and_dry_run_by_default(self):
        wf = WORKFLOW.read_text()
        self.assertIn("default: false", wf)
        self.assertIn("inputs.apply && inputs.confirm != 'LINK-1128-1129'", wf)
        self.assertIn("automations/content-sync/link_bf_pages.py", wf)
        self.assertIn("workflow_dispatch", wf)
        self.assertNotIn("schedule", wf)
        self.assertNotIn("push:", wf)

    def test_script_never_publishes_or_creates(self):
        src = SCRIPT.read_text()
        self.assertNotIn('"status": "publish"', src)
        self.assertNotIn("/wp/v2/pages\",", src)
        self.assertNotIn("set-language", src)
        self.assertNotIn("set-switcher", src)


if __name__ == "__main__":
    unittest.main()
