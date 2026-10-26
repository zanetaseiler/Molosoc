import importlib.util
import pathlib
import unittest

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
            pub.check({"slug": "other", "lang": "cz"}, "cz")
        pub.check({"slug": "vanocni-darek-molosoc", "lang": "cz"}, "cz")

    def test_workflow_gated_and_no_create(self):
        wf = (ROOT / ".github/workflows/publish-xmas-pages.yml").read_text()
        self.assertIn("PUBLISH-1065-1066", wf)
        self.assertNotIn("push:", wf)
        self.assertNotIn("requests.post(f\"{base}/wp-json/wp/v2/pages\"", (ROOT / "automations/content-sync/publish_xmas_pages.py").read_text())


if __name__ == "__main__":
    unittest.main()
