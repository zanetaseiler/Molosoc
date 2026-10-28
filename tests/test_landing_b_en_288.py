"""Issue #288: English Landing B + the guarded list/apply provisioning script.

Static checks on the theme files (no PHP runtime needed beyond `php -l` when present) and
behavioural checks of automations/content-sync/landing_b_en.py against an in-memory fake WP.
"""
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import types
import unittest

try:
    import requests  # noqa: F401
except ImportError:
    sys.modules["requests"] = types.ModuleType("requests")

ROOT = pathlib.Path(__file__).resolve().parents[1]
THEME = ROOT / "site/theme"
TPL = (THEME / "page-hydrating-foot-covers-molosoc.php").read_text(encoding="utf-8")
INC = (THEME / "inc/landing-b-en.php").read_text(encoding="utf-8")
BUY = (THEME / "inc/landing-b-buy.php").read_text(encoding="utf-8")
FUNCTIONS = (THEME / "functions.php").read_text(encoding="utf-8")
CZ_TPL = (THEME / "page-hydratacni-navleky-molosoc.php").read_text(encoding="utf-8")
SLUG = "hydrating-foot-covers-molosoc"

spec = importlib.util.spec_from_file_location("lbe", ROOT / "automations/content-sync/landing_b_en.py")
lbe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lbe)


class ThemeFiles(unittest.TestCase):
    def test_slug_and_template_follow_page_slug_convention(self):
        self.assertIn(f"return '{SLUG}';", INC)
        self.assertTrue((THEME / f"page-{SLUG}.php").exists())

    @unittest.skipUnless(shutil.which("php"), "php not installed")
    def test_php_syntax(self):
        for f in (f"page-{SLUG}.php", "inc/landing-b-en.php", "inc/landing-b-buy.php", "functions.php"):
            r = subprocess.run(["php", "-l", str(THEME / f)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_functions_php_only_gains_the_require(self):
        diff = subprocess.run(["git", "diff", "-U0", "origin/main", "--", "site/theme/functions.php"], cwd=ROOT, capture_output=True, text=True).stdout
        if not diff and not (ROOT / ".git").exists():
            self.skipTest("no git")
        removed = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
        self.assertEqual(removed, [])
        self.assertEqual(FUNCTIONS.count("/inc/landing-b-en.php';"), 1)
        schema_at = FUNCTIONS.index("/inc/landing-b-schema.php';")
        self.assertGreater(FUNCTIONS.index("/inc/landing-b-en.php';"), schema_at)  # needs molosoc_landing_b_schema_site_nodes()

    def test_cz_template_is_untouched_and_still_cz_only(self):
        self.assertIn("molosoc_landing_b_buy_cta(); ?>", CZ_TPL)  # default args = CZ, unchanged
        self.assertNotIn("'en'", CZ_TPL.split("get_header();")[0].split("defined( 'ABSPATH' )")[1])

    def test_assets_head_and_title_are_slug_gated_and_additive(self):
        self.assertIn("function molosoc_landing_b_en_active()", INC)
        self.assertIn("return is_page( molosoc_landing_b_en_slug() );", INC)
        for needle in ("landing-b.css", "landing-b.js", "wp_dequeue_style( 'molosoc-fonts' );",
                       "add_action( 'wp_head', 'molosoc_landing_b_en_head', 1 );", "media=\"print\" onload"):
            self.assertIn(needle, INC, needle)
        self.assertEqual(len(re.findall(r"add_filter\( 'pre_get_document_title'", INC)), 1)

    def test_no_redirects_canonical_or_robots_changes(self):
        for src in (INC, TPL):
            code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
            for bad in ("wp_redirect", "wp_safe_redirect", "template_redirect", "rel=\"canonical\"", "wp_robots", "noindex"):
                self.assertNotIn(bad, code, bad)


class TemplateContent(unittest.TestCase):
    def test_every_purchase_cta_is_english(self):
        self.assertGreaterEqual(TPL.count("molosoc_landing_b_buy_cta( '', 'en' )"), 6)
        self.assertNotIn("molosoc_landing_b_buy_cta()", TPL)
        self.assertNotIn("molosoc_product_url( 'cz' )", TPL)
        self.assertIn("'en' === $lang", BUY)
        self.assertIn("Continue to checkout", BUY)
        self.assertIn("Please choose a size.", BUY)

    def test_same_sections_as_cz_in_order(self):
        cz = re.findall(r'<section class="([^"]+)" aria-label', CZ_TPL)
        en = re.findall(r'<section class="([^"]+)" aria-label', TPL)
        self.assertEqual(en, cz)

    def test_no_czech_copy_or_cz_urls_left(self):
        body = TPL.split("get_header();")[1]
        self.assertIsNone(re.search(r"[ěščřžýáíéúůďťň]", body, flags=re.I), "Czech diacritics in EN template")
        self.assertNotIn("/cz/", body)
        self.assertNotIn(" Kč", body)

    def test_price_and_shipping_follow_the_en_product_page(self):
        self.assertIn("$lpb_price    = '€10';", TPL)
        self.assertIn("charged as 229 CZK", TPL)
        self.assertIn("Shipping from 69 CZK", TPL)
        shared = (THEME / "inc/woocommerce-lang.php").read_text(encoding="utf-8")
        self.assertIn("&euro;10 &middot; charged as 229 CZK", shared)
        self.assertIn("'Shipping from 69 CZK'", shared)

    def test_cz_only_claims_not_carried_over(self):
        for needle in ("lpb-strip__scarcity", "lpb-cod", "lpb-testimonial", "molosoc_cod_cz_text"):
            self.assertNotIn(needle, TPL, needle)

    def test_faq_single_source_matches_schema(self):
        self.assertIn("molosoc_landing_b_en_faq( $lpb_price, $lpb_shipping )", TPL)
        self.assertIn("molosoc_landing_b_en_faq( '€10', 'Shipping from 69 CZK' )", INC)
        self.assertEqual(len(re.findall(r"array\( '[^']+', '", INC.split("function molosoc_landing_b_en_faq")[1].split("function molosoc_landing_b_en_schema_graph")[0])), 6)

    def test_pillar_link_is_the_en_cracked_heels_page(self):
        self.assertIn("home_url( '/cracked-heels/' )", TPL)

    @unittest.skipUnless(shutil.which("php"), "php not installed")
    def test_schema_graph_is_valid_english_json_ld(self):
        php = r"""<?php
function molosoc_landing_b_schema_site_nodes() { return array( array( '@type' => 'Organization', '@id' => 'https://molosoc.com/#organization' ) ); }
define( 'ABSPATH', 1 );
function is_page() { return false; }
function add_filter() {}
function add_action() {}
require %s;
echo json_encode( molosoc_landing_b_en_schema_graph( 'https://molosoc.com/%s/', 'T', 'https://molosoc.com/product/moisture-lock-foot-cover/', molosoc_landing_b_en_faq( '€10', 'Shipping from 69 CZK' ) ), JSON_UNESCAPED_UNICODE );
""" % (json.dumps(str(THEME / "inc/landing-b-en.php")), SLUG)
        out = subprocess.run(["php"], input=php, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        g = json.loads(out.stdout)["@graph"]
        types_ = [n["@type"] for n in g]
        self.assertEqual(types_, ["Organization", "WebPage", "FAQPage"])
        self.assertEqual(g[1]["inLanguage"], "en")
        self.assertEqual(len(g[2]["mainEntity"]), 6)
        self.assertIn("€10 (charged as 229 CZK)", g[2]["mainEntity"][5]["acceptedAnswer"]["text"])


# ---------------------------------------------------------------- script ----------

class Resp:
    def __init__(self, status=200, data=None, text=""):
        self.status_code, self._d, self.text = status, data, text or (json.dumps(data) if data is not None else "")

    def json(self):
        if self._d is None:
            raise ValueError
        return self._d


class FakeWP:
    """Minimal in-memory WP: pages, Polylang helper, two menus, a public front end."""

    def __init__(self, helper=True, theme_deployed=True, en_exists=False):
        self.helper, self.theme_deployed = helper, theme_deployed
        self.public_status = 200
        self.public_raises = False
        self.calls = []
        self.pages = {1037: {"id": 1037, "slug": lbe.CZ_PAGE["slug"], "status": "publish", "link": "https://molosoc.com/cz/hydratacni-navleky-molosoc/"}}
        self.lang = {1037: "cz"}
        self.tr = {}
        if en_exists:
            self.pages[2001] = {"id": 2001, "slug": lbe.EN_SLUG, "status": "draft", "link": f"https://molosoc.com/{lbe.EN_SLUG}/"}
            self.lang[2001] = "en"
        self.menus = {
            68: [
                {"id": 904, "menu_order": 1, "parent": 0, "type": "custom", "object": "custom", "object_id": 904, "title": {"raw": "Návleky na nohy"}, "url": "https://molosoc.com/cz/navleky-na-nohy/"},
                {"id": 905, "menu_order": 2, "parent": 904, "type": "post_type", "object": "page", "object_id": 886, "title": {"raw": "Návlek na nohy"}, "url": "https://molosoc.com/cz/navleky-na-nohy/hydratacni-navlek-na-nohy/"},
                {"id": 906, "menu_order": 5, "parent": 0, "type": "custom", "object": "custom", "object_id": 906, "title": {"raw": "Languages"}, "url": "#pll_switcher"},
            ],
            67: [
                {"id": 810, "menu_order": 1, "parent": 0, "type": "post_type", "object": "page", "object_id": 869, "title": {"raw": ""}, "url": "https://molosoc.com/foot-covers/moisture-lock-foot-cover/"},
                {"id": 811, "menu_order": 5, "parent": 0, "type": "custom", "object": "custom", "object_id": 811, "title": {"raw": "Languages"}, "url": "#pll_switcher"},
            ],
        }
        self.menus[67][0]["title"] = {"raw": "Foot Covers"}

    def _menu_item(self, iid):
        for items in self.menus.values():
            for i in items:
                if i["id"] == iid:
                    return i

    # Client interface
    def get(self, path, **params):
        m = re.match(r"/wp-json/wp/v2/pages/(\d+)", path)
        if m:
            return Resp(200, self.pages[int(m.group(1))])
        if path == "/wp-json/wp/v2/pages":
            return Resp(200, [p for p in self.pages.values() if p["slug"] == params.get("slug")])
        m = re.match(r"/wp-json/molosoc-migrate/v1/status/(\d+)", path)
        if m:
            if not self.helper:
                return Resp(404, {"code": "rest_no_route"})
            pid = int(m.group(1))
            return Resp(200, {"language": self.lang.get(pid), "translations": self.tr.get(pid, {})})
        if path == "/wp-json/wp/v2/menu-items":
            return Resp(200, [dict(i) for i in self.menus[int(params["menus"])]])
        raise AssertionError(path)

    def post(self, path, json):
        self.calls.append((path, json))
        if path == "/wp-json/wp/v2/pages":
            self.pages[2001] = {"id": 2001, "slug": json["slug"], "status": json["status"], "link": f"https://molosoc.com/{json['slug']}/"}
            self.lang[2001] = "en"
            return Resp(201, self.pages[2001])
        m = re.match(r"/wp-json/wp/v2/pages/(\d+)", path)
        if m:
            self.pages[int(m.group(1))].update(json)
            return Resp(200, self.pages[int(m.group(1))])
        if path.endswith("/link-translations"):
            t = json["translations"]
            for lang, pid in t.items():
                self.tr[pid] = {k: v for k, v in t.items()}
            return Resp(200, {"saved": t})
        m = re.match(r"/wp-json/wp/v2/menu-items/(\d+)", path)
        if m:
            it = self._menu_item(int(m.group(1)))
            if "title" in json:
                it["title"] = {"raw": json["title"]}
            if "object_id" in json:
                it["object_id"] = json["object_id"]
                it["url"] = self.pages[json["object_id"]]["link"]
            if "url" in json:
                it["url"] = json["url"]
            return Resp(200, it)
        raise AssertionError(path)

    def public(self, url):
        if self.public_raises:
            raise ConnectionError("simulated timeout")
        if self.pages.get(2001, {}).get("status") != "publish":
            return Resp(404, text="nope")
        if self.public_status != 200:
            return Resp(self.public_status, text="error")
        title = "<title>Reusable Hydrating Foot Mask | Molosoc</title>"
        # the document title is filtered globally; only the real EN template renders the body marker
        return Resp(200, text=title + ('<main data-lpb-en-landing="288">' if self.theme_deployed else "<main>other template</main>"))

    def writes(self):
        return list(self.calls)


class Script(unittest.TestCase):
    def run_apply(self, wp):
        st = lbe.report(wp)
        return lbe.apply(wp, st, 905, 810)

    def test_wp_url_must_be_exactly_production(self):
        for u in ("https://staging.molosoc.com", "http://molosoc.com", "https://molosoc.com/wp", ""):
            with self.assertRaises(SystemExit):
                lbe.validate_url(u)
        lbe.validate_url("https://molosoc.com")

    def test_list_is_read_only_and_marks_candidates(self):
        wp = FakeWP()
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            lbe.report(wp)
        out = buf.getvalue()
        self.assertEqual(wp.calls, [])
        self.assertIn("id=905", out)
        self.assertIn("id=810", out)
        self.assertEqual(out.count("points at Landing Page A (candidate)"), 2)
        self.assertIn("does not exist yet", out)

    def test_apply_refuses_without_confirm_or_ids(self):
        import os
        os.environ.update(WP_URL="https://molosoc.com", WP_USER="u", WP_APP_PASSWORD="p")
        for argv in (["apply"], ["apply", "--cz-menu-item", "1", "--en-menu-item", "2"], ["apply", "--confirm", lbe.CONFIRM]):
            with self.assertRaises(SystemExit):
                lbe.main(argv)

    def test_without_polylang_helper_nothing_is_written(self):
        wp = FakeWP(helper=False)
        self.assertEqual(self.run_apply(wp), 3)
        self.assertEqual(wp.writes(), [])

    def test_wrong_menu_item_is_refused_before_any_write(self):
        wp = FakeWP()
        st = lbe.report(wp)
        # 904 (the parent "Návleky na nohy" custom link) and 906 (language switcher) are not Landing A links.
        for bad in (904, 906):
            self.assertEqual(lbe.apply(wp, st, bad, 810), 3)
        self.assertEqual(lbe.apply(wp, st, 905, 811), 3)
        self.assertEqual(lbe.apply(wp, st, 905, 12345), 3)
        self.assertEqual(wp.writes(), [])

    def test_happy_path_creates_links_publishes_then_repoints_only_two_items(self):
        wp = FakeWP()
        before_other = {i["id"]: dict(i) for m in wp.menus.values() for i in m if i["id"] in (904, 906, 811)}
        self.assertEqual(self.run_apply(wp), 0)
        order = [p for p, _ in wp.calls]
        self.assertEqual(order[0], "/wp-json/wp/v2/pages")                    # draft first
        self.assertEqual(wp.calls[0][1]["status"], "draft")
        self.assertIn("/wp-json/molosoc-migrate/v1/link-translations", order)
        self.assertLess(order.index("/wp-json/molosoc-migrate/v1/link-translations"), order.index("/wp-json/wp/v2/pages/2001"))
        self.assertLess(order.index("/wp-json/wp/v2/pages/2001"), order.index("/wp-json/wp/v2/menu-items/905"))
        self.assertEqual(wp.tr[1037], {"cz": 1037, "en": 2001})
        self.assertEqual(sorted(p for p in order if "menu-items" in p), ["/wp-json/wp/v2/menu-items/810", "/wp-json/wp/v2/menu-items/905"])
        # CZ item -> CZ B, EN item -> EN B, labels/parents/order kept
        cz = wp._menu_item(905)
        en = wp._menu_item(810)
        self.assertEqual((cz["object_id"], cz["title"]["raw"], cz["parent"], cz["menu_order"]), (1037, "Návlek na nohy", 904, 2))
        self.assertEqual((en["object_id"], en["title"]["raw"], en["menu_order"]), (2001, "Foot Covers", 1))
        for iid, row in before_other.items():
            self.assertEqual(wp._menu_item(iid), row)
        # no delete / redirect style calls anywhere
        self.assertFalse([p for p in order if "redirect" in p.lower()])

    def test_is_idempotent(self):
        wp = FakeWP()
        self.assertEqual(self.run_apply(wp), 0)
        n = len(wp.calls)
        wp.pages[2001]["status"] = "publish"
        st = lbe.report(wp)
        self.assertEqual(lbe.apply(wp, st, 905, 810), 0)
        # second run: no new page, no new link, no publish; only the (no-op) menu updates
        later = [p for p, _ in wp.calls[n:]]
        self.assertNotIn("/wp-json/wp/v2/pages", later)
        self.assertNotIn("/wp-json/molosoc-migrate/v1/link-translations", later)

    def test_missing_theme_reverts_to_draft_and_touches_no_menu(self):
        wp = FakeWP(theme_deployed=False)
        with self.assertRaises(lbe.Abort):
            self.run_apply(wp)
        self.assertEqual(wp.pages[2001]["status"], "draft")
        self.assertFalse([p for p, _ in wp.calls if "menu-items" in p])

    def test_wrong_template_with_matching_title_is_not_verified(self):
        # title filter fires, but the body is not the EN Landing B template -> must not pass
        wp = FakeWP(theme_deployed=False)
        with self.assertRaises(lbe.Abort):
            self.run_apply(wp)
        self.assertEqual(wp.pages[2001]["status"], "draft")
        self.assertFalse([p for p, _ in wp.calls if "menu-items" in p])

    def test_rerun_with_transient_http_failure_keeps_published_page(self):
        wp = FakeWP()
        self.assertEqual(self.run_apply(wp), 0)
        self.assertEqual(wp.pages[2001]["status"], "publish")
        n = len(wp.calls)
        wp.public_status = 503
        st = lbe.report(wp)
        with self.assertRaises(lbe.Abort):
            lbe.apply(wp, st, 905, 810)
        self.assertEqual(wp.pages[2001]["status"], "publish")
        later = wp.calls[n:]
        self.assertFalse([p for p, j in later if j.get("status") == "draft"])
        self.assertFalse([p for p, _ in later if "menu-items" in p])

    def test_public_request_raising_after_our_publish_reverts_to_draft(self):
        wp = FakeWP()
        wp.public_raises = True
        with self.assertRaises(lbe.Abort):
            self.run_apply(wp)
        self.assertEqual(wp.pages[2001]["status"], "draft")
        self.assertFalse([p for p, _ in wp.calls if "menu-items" in p])

    def test_rerun_with_public_request_raising_keeps_published_page(self):
        wp = FakeWP()
        self.assertEqual(self.run_apply(wp), 0)
        n = len(wp.calls)
        wp.public_raises = True
        st = lbe.report(wp)
        with self.assertRaises(lbe.Abort):
            lbe.apply(wp, st, 905, 810)
        self.assertEqual(wp.pages[2001]["status"], "publish")
        self.assertFalse([p for p, j in wp.calls[n:] if j.get("status") == "draft" or "menu-items" in p])

    def test_rerun_with_wrong_template_keeps_published_page(self):
        wp = FakeWP()
        self.assertEqual(self.run_apply(wp), 0)
        n = len(wp.calls)
        wp.theme_deployed = False
        st = lbe.report(wp)
        with self.assertRaises(lbe.Abort):
            lbe.apply(wp, st, 905, 810)
        self.assertEqual(wp.pages[2001]["status"], "publish")
        self.assertFalse([p for p, _ in wp.calls[n:] if "menu-items" in p])

    def test_rejected_rollback_is_reported_not_masked(self):
        wp = FakeWP()
        wp.public_status = 503
        orig = wp.post

        def post(path, json):
            if json.get("status") == "draft" and path.endswith("/2001"):
                wp.calls.append((path, json))
                return Resp(503, text="unavailable")
            return orig(path, json)

        wp.post = post
        with self.assertRaises(lbe.Abort) as cm:
            self.run_apply(wp)
        self.assertIn("FAILED", str(cm.exception))
        self.assertIn("manually", str(cm.exception))
        self.assertNotIn("was set back to draft", str(cm.exception))
        self.assertFalse([p for p, _ in wp.calls if "menu-items" in p])

    def test_cz_page_with_other_en_translation_is_refused(self):
        wp = FakeWP()
        wp.tr[1037] = {"cz": 1037, "en": 999}
        self.assertEqual(self.run_apply(wp), 3)
        self.assertEqual(wp.writes(), [])

    def test_cz_page_with_other_en_translation_is_refused_when_en_page_exists(self):
        wp = FakeWP(en_exists=True)
        wp.tr[1037] = {"cz": 1037, "en": 999}
        self.assertEqual(self.run_apply(wp), 3)
        self.assertEqual(wp.writes(), [])

    def test_template_renders_the_body_marker_the_script_checks(self):
        tpl = (ROOT / "site/theme/page-hydrating-foot-covers-molosoc.php").read_text()
        self.assertIn(lbe.EN_BODY_MARKER, tpl)

    def test_existing_en_page_of_wrong_language_is_refused(self):
        wp = FakeWP(en_exists=True)
        wp.lang[2001] = "cz"
        self.assertEqual(self.run_apply(wp), 3)
        self.assertEqual(wp.writes(), [])

    def test_workflow_is_dispatch_only_list_by_default_and_gated(self):
        wf = (ROOT / ".github/workflows/provision-en-lp-b.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", wf)
        self.assertNotIn("push:", wf)
        self.assertNotIn("schedule:", wf)
        self.assertIn("default: list", wf)
        self.assertIn("APPLY-LANDING-B-288", wf)
        self.assertIn("PROD_WP_URL", wf)


if __name__ == "__main__":
    unittest.main()
