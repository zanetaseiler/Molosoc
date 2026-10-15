"""Issue #198: Czech copy for the empty-cart headings (page 1012) and the
"Dobírka" (COD) description/instructions.

Two mechanisms, two sets of static checks (no PHP runtime, no network):

1. site/theme/inc/woocommerce-lang.php, section 9 — a per-language
   `woocommerce_gateway_description` filter for gateway `cod`, plus a
   priority-9/11 swap of the COD gateway's `$instructions` property around
   WooCommerce's own thank-you / email outputs (WooCommerce has no filter for
   instructions). The stored settings (title "Dobírka", enable_for_methods,
   gateway order) must never be read-filtered or written.

2. automations/content-sync/translate_cz_cart_empty_state.py — the
   dispatch-only script that replaces exactly the two heading texts in page
   1012's saved block markup. Its pure function is exercised directly; its
   main() is driven with a fake `requests` to prove the dry run never writes
   and the apply path writes once and re-verifies.
"""
import importlib.util
import io
import re
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LANG_PHP = ROOT / "site/theme/inc/woocommerce-lang.php"
SCRIPT_DIR = ROOT / "automations/content-sync"
SCRIPT = SCRIPT_DIR / "translate_cz_cart_empty_state.py"
WORKFLOW = ROOT / ".github/workflows/translate-cz-cart-empty-state.yml"

CZ_COD_TEXT = "Zaplatíte při převzetí zásilky."
CZ_EMPTY = "Váš košík je zatím prázdný."
CZ_NEW = "Novinky v obchodě"

# Realistic excerpt of the live page-1012 empty-cart block markup (Cart block
# inner blocks as WordPress saves them).
SAMPLE_RAW = """<!-- wp:woocommerce/cart -->
<div class="wp-block-woocommerce-cart alignwide is-loading"><!-- wp:woocommerce/filled-cart-block -->
<div class="wp-block-woocommerce-filled-cart-block"></div>
<!-- /wp:woocommerce/filled-cart-block -->

<!-- wp:woocommerce/empty-cart-block -->
<div class="wp-block-woocommerce-empty-cart-block"><!-- wp:heading {"textAlign":"center","className":"with-empty-cart-icon wc-block-cart__empty-cart__title"} -->
<h2 class="wp-block-heading has-text-align-center with-empty-cart-icon wc-block-cart__empty-cart__title">Your cart is currently empty!</h2>
<!-- /wp:heading -->

<!-- wp:separator {"className":"is-style-dots"} -->
<hr class="wp-block-separator has-alpha-channel-opacity is-style-dots"/>
<!-- /wp:separator -->

<!-- wp:heading {"textAlign":"center"} -->
<h2 class="wp-block-heading has-text-align-center">New in store</h2>
<!-- /wp:heading -->

<!-- wp:woocommerce/product-new {"columns":4,"rows":1} /--></div>
<!-- /wp:woocommerce/empty-cart-block --></div>
<!-- /wp:woocommerce/cart -->"""


def php_function_body(src, name):
    match = re.search(r"function %s\s*\((.*?)\)\s*\{(.*?)\n\}" % re.escape(name), src, re.S)
    assert match, "%s() not found" % name
    return match.group(1), match.group(2)


def load_script():
    sys.path.insert(0, str(SCRIPT_DIR))  # sibling import of create_cart_checkout_cz_pages
    spec = importlib.util.spec_from_file_location("translate_cz_cart_empty_state", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CodCzechTextPhpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = LANG_PHP.read_text(encoding="utf-8")

    def test_czech_text_is_exactly_the_issue_string(self):
        _, body = php_function_body(self.src, "molosoc_cod_cz_text")
        self.assertIn("return '%s';" % CZ_COD_TEXT, body)
        # One string for both description and instructions: no second literal.
        self.assertEqual(self.src.count(CZ_COD_TEXT), 1)

    def test_description_filter_registered_once_for_two_args(self):
        self.assertRegex(
            self.src,
            r"add_filter\(\s*'woocommerce_gateway_description',\s*'molosoc_cz_cod_gateway_description',\s*10,\s*2\s*\);",
        )
        # The pre-existing EN filter stays registered and untouched.
        self.assertRegex(
            self.src,
            r"add_filter\(\s*'woocommerce_gateway_description',\s*'molosoc_en_gateway_description',\s*10,\s*2\s*\);",
        )
        self.assertEqual(self.src.count("add_filter( 'woocommerce_gateway_description'"), 2)

    def test_description_filter_gates_on_cod_and_explicit_cz(self):
        params, body = php_function_body(self.src, "molosoc_cz_cod_gateway_description")
        self.assertRegex(params, r"\$description,\s*\$gateway_id = ''")
        self.assertIn("'cod' !== (string) $gateway_id", body)
        self.assertIn("'cz' !== pll_current_language()", body)
        self.assertIn("function_exists( 'pll_current_language' )", body)
        # A blanked stored description stays blank; otherwise the Czech text.
        self.assertIn("'' === trim( (string) $description )", body)
        self.assertRegex(body, r"return molosoc_cod_cz_text\(\);\s*$")
        self.assertNotIn("'en'", body)

    def test_instruction_swap_hooks_bracket_woocommerce_at_9_and_11(self):
        for hook, before, after, args in (
            ("woocommerce_thankyou_cod", "molosoc_cz_cod_thankyou_before", "molosoc_cz_cod_thankyou_after", ""),
            (
                "woocommerce_email_before_order_table",
                "molosoc_cz_cod_email_before",
                "molosoc_cz_cod_email_after",
                r",\s*3",
            ),
        ):
            self.assertRegex(self.src, r"add_action\(\s*'%s',\s*'%s',\s*9%s\s*\);" % (hook, before, args))
            self.assertRegex(self.src, r"add_action\(\s*'%s',\s*'%s',\s*11%s\s*\);" % (hook, after, args))
        # Both "after" callbacks restore unconditionally (no-op when nothing stashed).
        for fn in ("molosoc_cz_cod_thankyou_after", "molosoc_cz_cod_email_after"):
            _, body = php_function_body(self.src, fn)
            self.assertEqual(body.strip(), "molosoc_cod_swap_instructions( false );")

    def test_swap_only_for_czech_orders_and_customer_emails(self):
        _, body = php_function_body(self.src, "molosoc_cz_cod_email_before")
        self.assertIn("$sent_to_admin", body)
        self.assertIn("'cod' !== $order->get_payment_method()", body)
        self.assertIn("molosoc_order_is_cz( $order )", body)

        _, body = php_function_body(self.src, "molosoc_cz_cod_thankyou_before")
        self.assertIn("molosoc_order_is_cz( wc_get_order( $order_id ), true )", body)

        _, body = php_function_body(self.src, "molosoc_order_is_cz")
        self.assertIn("$order->get_meta( '_molosoc_lang' )", body)
        self.assertIn("'cz' === $lang", body)
        self.assertIn("$order instanceof WC_Order", body)

    def test_swap_stashes_and_restores_the_property(self):
        _, body = php_function_body(self.src, "molosoc_cod_swap_instructions")
        self.assertIn("static $saved = null;", body)
        self.assertIn("$saved             = $cod->instructions;", body)
        self.assertIn("$cod->instructions = molosoc_cod_cz_text();", body)
        self.assertIn("$cod->instructions = $saved;", body)
        self.assertIn("'' === trim( (string) $cod->instructions )", body)

    def test_stored_gateway_settings_are_never_touched(self):
        section = self.src[self.src.index("9. \"Dobírka\"") :]
        # Code only: the doc comments legitimately name the settings they promise not to touch.
        section = re.sub(r"/\*.*?\*/", "", section, flags=re.S)
        section = re.sub(r"^\s*//.*$", "", section, flags=re.M)
        for forbidden in (
            "update_option",
            "option_woocommerce_cod_settings",
            "pre_option",
            "woocommerce_cod_settings",
            "update_meta_data",
            "enable_for_methods",
            "woocommerce_gateway_title",
            "woocommerce_payment_gateways",
        ):
            self.assertNotIn(forbidden, section, forbidden)
        # Title stays "Dobírka": no Czech title literal anywhere in the file.
        self.assertNotIn("'Dobírka'", self.src)


@unittest.skipUnless(SCRIPT.exists(), "script missing")
class TranslateCartContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_script()

    def test_constants_match_the_issue(self):
        self.assertEqual(self.mod.PAGE_ID, 1012)
        self.assertEqual(self.mod.EXPECTED_SLUG, "kosik")
        self.assertEqual(self.mod.EXPECTED_PATH, "/cz/kosik/")
        self.assertEqual(self.mod.EN_TWIN_ID, 359)
        self.assertEqual(
            self.mod.REPLACEMENTS,
            (
                (">Your cart is currently empty!</h2>", ">%s</h2>" % CZ_EMPTY),
                (">New in store</h2>", ">%s</h2>" % CZ_NEW),
            ),
        )

    def test_replaces_both_headings_and_nothing_else(self):
        out, changed = self.mod.translate_cart_content(SAMPLE_RAW)
        self.assertEqual(len(changed), 2)
        self.assertIn(">%s</h2>" % CZ_EMPTY, out)
        self.assertIn(">%s</h2>" % CZ_NEW, out)
        self.assertNotIn("Your cart is currently empty!", out)
        self.assertNotIn("New in store", out)
        # Reversing only the two text swaps gives back the original byte for
        # byte: block comments, attributes and classes are untouched.
        reverted = out
        for old, new in changed:
            reverted = reverted.replace(new, old, 1)
        self.assertEqual(reverted, SAMPLE_RAW)
        self.assertIn('"className":"with-empty-cart-icon wc-block-cart__empty-cart__title"', out)

    def test_idempotent_second_pass_changes_nothing(self):
        out, _ = self.mod.translate_cart_content(SAMPLE_RAW)
        again, changed = self.mod.translate_cart_content(out)
        self.assertEqual(again, out)
        self.assertEqual(changed, [])

    def test_partially_translated_page_finishes_the_other_heading(self):
        half = SAMPLE_RAW.replace(">New in store</h2>", ">%s</h2>" % CZ_NEW)
        out, changed = self.mod.translate_cart_content(half)
        self.assertEqual([old for old, _ in changed], [">Your cart is currently empty!</h2>"])
        self.assertEqual(out.count(">%s</h2>" % CZ_NEW), 1)

    def test_missing_or_duplicated_heading_refuses(self):
        with self.assertRaises(self.mod.ContentMismatch):
            self.mod.translate_cart_content(SAMPLE_RAW.replace(">New in store</h2>", ">Novinky</h2>"))
        with self.assertRaises(self.mod.ContentMismatch):
            self.mod.translate_cart_content(SAMPLE_RAW.replace(
                "<!-- /wp:woocommerce/empty-cart-block -->",
                '<!-- wp:heading -->\n<h2>New in store</h2>\n<!-- /wp:heading -->\n<!-- /wp:woocommerce/empty-cart-block -->',
            ))
        with self.assertRaises(self.mod.ContentMismatch):
            self.mod.translate_cart_content("")

    def test_phrase_outside_empty_cart_block_is_never_touched(self):
        outside = (
            '<!-- wp:heading -->\n<h2 class="wp-block-heading">New in store</h2>\n<!-- /wp:heading -->\n'
        )
        # Heading removed from the empty-cart block, same phrase elsewhere once:
        # must refuse rather than rewrite the unrelated heading.
        gone = SAMPLE_RAW.replace(">New in store</h2>", ">Novinky</h2>") + "\n" + outside
        with self.assertRaises(self.mod.ContentMismatch):
            self.mod.translate_cart_content(gone)
        # Phrase also present outside while the real one exists: outside is left alone.
        both = SAMPLE_RAW + "\n" + outside
        out, changed = self.mod.translate_cart_content(both)
        self.assertEqual(len(changed), 2)
        self.assertTrue(out.endswith(outside))
        self.assertEqual(out.count("New in store"), 1)

    def test_heading_must_be_a_heading_block_in_the_empty_cart_block(self):
        bare = SAMPLE_RAW.replace(
            '<!-- wp:heading {"textAlign":"center"} -->\n<h2 class="wp-block-heading has-text-align-center">New in store</h2>',
            '<h2>New in store</h2>',
        )
        with self.assertRaises(self.mod.ContentMismatch):
            self.mod.translate_cart_content(bare)
        with self.assertRaises(self.mod.ContentMismatch):
            self.mod.translate_cart_content(SAMPLE_RAW.replace("wp:woocommerce/empty-cart-block", "wp:woocommerce/other"))

    def _fake_requests(self, pages, post_status=200, stored_after_post=None):
        """A requests stand-in serving `pages` ({id: (json, raw)}) and
        recording POSTs. After a POST, page 1012's raw becomes
        `stored_after_post` (default: exactly the posted content)."""
        mod = self.mod
        calls = {"post": []}

        def page_json(page_id):
            data, raw = pages[page_id]
            return dict(data, content={"raw": raw})

        def fake_get(url, params=None, auth=None, timeout=None):
            page_id = int(url.rstrip("/").rsplit("/", 1)[1])
            resp = mock.Mock(status_code=200)
            resp.json.return_value = page_json(page_id)
            resp.raise_for_status.return_value = None
            return resp

        def fake_post(url, json=None, auth=None, timeout=None):
            calls["post"].append((url, json))
            data, _ = pages[mod.PAGE_ID]
            new_raw = json["content"] if stored_after_post is None else stored_after_post
            pages[mod.PAGE_ID] = (data, new_raw)
            return mock.Mock(status_code=post_status, text="")

        fake = mock.Mock()
        fake.get.side_effect = fake_get
        fake.post.side_effect = fake_post
        return fake, calls

    def _pages(self, raw_1012=SAMPLE_RAW):
        return {
            1012: ({"id": 1012, "slug": "kosik", "status": "publish", "link": "https://molosoc.com/cz/kosik/"}, raw_1012),
            359: ({"id": 359, "slug": "cart", "status": "publish", "link": "https://molosoc.com/cart/"}, SAMPLE_RAW),
        }

    def _run(self, argv, pages, **fake_kwargs):
        fake, calls = self._fake_requests(pages, **fake_kwargs)
        out = io.StringIO()
        with mock.patch.object(self.mod, "requests", fake), mock.patch.object(
            self.mod, "verify_target_is_production"
        ) as verify, mock.patch.object(self.mod, "wp_auth", return_value=("u", "p")), mock.patch.object(
            self.mod, "WP_URL", "https://molosoc.com"
        ), redirect_stdout(out):
            try:
                code = self.mod.main(argv)
            except SystemExit as exc:
                code = exc.code
        verify.assert_called_once_with()
        return code, calls, out.getvalue()

    def test_dry_run_reads_and_never_writes(self):
        pages = self._pages()
        code, calls, log = self._run([], pages)
        self.assertEqual(code, 0)
        self.assertEqual(calls["post"], [])
        self.assertIn("DRY RUN", log)
        self.assertIn(CZ_EMPTY, log)
        self.assertEqual(pages[1012][1], SAMPLE_RAW)

    def test_apply_writes_page_1012_once_and_verifies_reread(self):
        pages = self._pages()
        code, calls, log = self._run(["--apply"], pages)
        self.assertEqual(code, 0)
        self.assertEqual(len(calls["post"]), 1)
        url, payload = calls["post"][0]
        self.assertTrue(url.endswith("/wp-json/wp/v2/pages/1012"))
        self.assertEqual(list(payload), ["content"])  # content only: status/title/slug untouched
        self.assertIn(">%s</h2>" % CZ_EMPTY, payload["content"])
        self.assertIn("Verified: re-read content", log)
        self.assertEqual(pages[359][1], SAMPLE_RAW)  # EN twin only read

    def test_apply_fails_loudly_when_wordpress_alters_the_save(self):
        pages = self._pages()
        code, calls, log = self._run(["--apply"], pages, stored_after_post=SAMPLE_RAW + " ")
        self.assertNotEqual(code, 0)
        self.assertEqual(len(calls["post"]), 1)
        self.assertIn("Revisions", str(code))

    def test_refuses_wrong_page_before_any_write(self):
        pages = self._pages()
        data, raw = pages[1012]
        pages[1012] = (dict(data, slug="cart", link="https://molosoc.com/cart/"), raw)
        code, calls, _ = self._run(["--apply"], pages)
        self.assertNotEqual(code, 0)
        self.assertIn("REFUSING", str(code))
        self.assertEqual(calls["post"], [])

    def test_already_translated_page_is_a_noop(self):
        translated, _ = self.mod.translate_cart_content(SAMPLE_RAW)
        pages = self._pages(raw_1012=translated)
        code, calls, log = self._run(["--apply"], pages)
        self.assertEqual(code, 0)
        self.assertEqual(calls["post"], [])
        self.assertIn("nothing to do", log)


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.yml = WORKFLOW.read_text(encoding="utf-8")

    def test_dispatch_only_with_apply_input(self):
        on_block = re.search(r"^on:\n(.*?)^jobs:", self.yml, re.S | re.M).group(1)
        self.assertIn("workflow_dispatch:", on_block)
        for trigger in ("push:", "pull_request:", "schedule:", "issue_comment:"):
            self.assertNotIn(trigger, on_block)
        self.assertRegex(on_block, r"apply:\n(.*\n){1,4}\s*type: boolean")
        self.assertRegex(on_block, r"default: false")

    def test_runs_script_against_production_secrets_and_gates_apply(self):
        self.assertIn("secrets.PROD_WP_URL", self.yml)
        self.assertIn("secrets.PROD_WP_USER", self.yml)
        self.assertIn("secrets.PROD_WP_APP_PASSWORD", self.yml)
        self.assertIn("APPLY: ${{ inputs.apply }}", self.yml)
        self.assertIn('if [ "$APPLY" = "true" ]; then', self.yml)
        self.assertEqual(self.yml.count("python3 automations/content-sync/translate_cz_cart_empty_state.py"), 2)
        self.assertEqual(self.yml.count("translate_cz_cart_empty_state.py --apply"), 1)


if __name__ == "__main__":
    unittest.main()
