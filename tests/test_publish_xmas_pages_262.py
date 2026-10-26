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
spec = importlib.util.spec_from_file_location("pub", ROOT / "automations/content-sync/publish_xmas_pages.py")
pub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pub)


class PublishXmas262(unittest.TestCase):
    def test_ids(self):
        self.assertEqual((pub.PAGES["cz"]["id"], pub.PAGES["en"]["id"]), (1065, 1066))

    def test_refuses_wrong_host(self):
        for u in ("https://staging.molosoc.com", "http://molosoc.com", "https://molosoc.com/x", ""):
            with self.assertRaises(SystemExit):
                pub.validate_url(u)
        pub.validate_url("https://molosoc.com")

    def test_refuses_wrong_page(self):
        with self.assertRaises(SystemExit):
            pub.check({"slug": "other"}, {"language": "cz"}, "cz")
        with self.assertRaises(SystemExit):
            pub.check({"slug": "vanocni-darek-molosoc"}, {"language": None}, "cz")
        pub.check({"slug": "vanocni-darek-molosoc"}, {"language": "cz"}, "cz")

    def test_uses_migration_helper_for_polylang(self):
        src = (ROOT / "automations/content-sync/publish_xmas_pages.py").read_text()
        self.assertIn("molosoc-migrate/v1/status/", src)
        self.assertIn("molosoc-migrate/v1/link-translations", src)

    def _resp(self, status, body=None, bad_json=False):
        class R:
            status_code = status

            def json(self_):
                if bad_json:
                    raise ValueError("no json")
                return body

            def raise_for_status(self_):
                if status >= 400:
                    raise RuntimeError(f"HTTP {status}")

        return R()

    def _get_pll(self, resp):
        orig = getattr(pub.requests, "get", None)
        pub.requests.get = lambda *a, **k: resp
        try:
            return pub.get_pll("https://molosoc.com", ("u", "p"), 1065)
        finally:
            if orig is None:
                del pub.requests.get
            else:
                pub.requests.get = orig

    def test_missing_endpoint_aborts_with_diagnosis(self):
        for resp in (self._resp(404, {"code": "rest_no_route"}), self._resp(404, bad_json=True)):
            with self.assertRaises(SystemExit) as cm:
                self._get_pll(resp)
            self.assertIn("deploy-helper", str(cm.exception))
            self.assertIn("rest_no_route", str(cm.exception))

    def test_missing_post_is_not_reported_as_missing_endpoint(self):
        with self.assertRaises(RuntimeError):
            self._get_pll(self._resp(404, {"code": "no_post"}))

    def test_ok_response_returned(self):
        self.assertEqual(self._get_pll(self._resp(200, {"language": "cz"})), {"language": "cz"})

    def test_no_write_on_missing_endpoint(self):
        calls = []
        orig = getattr(pub.requests, "post", None)
        pub.requests.post = lambda *a, **k: calls.append(a)
        try:
            with self.assertRaises(SystemExit):
                self._get_pll(self._resp(404, {"code": "rest_no_route"}))
        finally:
            if orig is None:
                del pub.requests.post
            else:
                pub.requests.post = orig
        self.assertEqual(calls, [])

    def test_workflow_gated_and_no_create(self):
        wf = (ROOT / ".github/workflows/publish-xmas-pages.yml").read_text()
        self.assertIn("PUBLISH-1065-1066", wf)
        self.assertNotIn("push:", wf)
        self.assertNotIn("requests.post(f\"{base}/wp-json/wp/v2/pages\"", (ROOT / "automations/content-sync/publish_xmas_pages.py").read_text())


if __name__ == "__main__":
    unittest.main()
