"""Issue #341: CZ/EN checkout explanation, default/declined review request,
no newsletter coupling, no payment changes, Terms/Privacy copy."""
import re, shutil, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_review_request_333 import run, MODULE, LIVE  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SHOWN = {"molosoc_review_request_notice_shown": "1"}


def checkout(post, lang="cz", mode="live"):
    return run(opts={"molosoc_review_request_mode": mode}, meta={"_molosoc_review_request_notice": ""},
               checkout=True, post=post, lang=lang, runs=0)


@unittest.skipUnless(shutil.which("php"), "php not installed")
class CheckoutNotice341(unittest.TestCase):
    def test_cz_en_explain_transactional_vs_review_and_link_privacy(self):
        cz = checkout(SHOWN)["html"]
        en = checkout(SHOWN, "en")["html"]
        self.assertIn("automaticky", cz); self.assertIn("newsletter", cz)
        self.assertIn("/zasady-ochrany-osobnich-udaju/", cz)
        self.assertIn("automatically", en); self.assertIn("not a newsletter", en)
        self.assertIn("/privacy-policies/", en)
        self.assertIn("not marketing consent", en)

    def test_default_keeps_order_eligible_and_declined_blocks_it(self):
        d = checkout(SHOWN)
        self.assertTrue(d["meta"]["_molosoc_review_request_notice"])
        self.assertNotIn("_molosoc_review_request_optout", d["meta"])
        n = checkout(dict(SHOWN, molosoc_review_request_refuse="1", billing_email="a@example.cz"), "en")
        self.assertTrue(n["meta"]["_molosoc_review_request_optout"])
        # persisted per order: declined order never mails even in live mode
        self.assertEqual(run(opts=LIVE, meta={"_molosoc_review_request_optout": "1"})["mails"], [])

    def test_off_mode_shows_nothing_and_nobody_eligible(self):
        self.assertEqual(checkout(SHOWN, mode="off")["html"], "")
        self.assertEqual(run(opts=LIVE, meta={"_molosoc_review_request_notice": ""})["mails"], [])

    def test_no_newsletter_coupling_and_no_payment_hooks(self):
        r = checkout(dict(SHOWN, molosoc_review_request_refuse="1", billing_email="a@example.cz"))
        self.assertEqual([k for k in r["opts"] if "newsletter" in k.lower() or "brevo" in k.lower()], [])
        self.assertFalse([k for k in r["meta"] if "newsletter" in k.lower()])
        code = MODULE.read_text(encoding="utf-8")
        hooks = re.findall(r"add_(?:action|filter)\(\s*'([a-z_]+)'", code)
        self.assertFalse([h for h in hooks if re.search(r"payment|fee|gateway|total|cart|coupon", h)])
        self.assertNotIn("add_fee", code)
        self.assertNotIn("woocommerce_checkout_process", code)  # never blocks checkout
        self.assertNotIn("wc_add_notice", code)


class LegalCopy341(unittest.TestCase):
    def test_cz_terms_and_privacy(self):
        t = (ROOT / "seo/cz-pages/terms-of-service.md").read_text(encoding="utf-8")
        p = (ROOT / "seo/cz-pages/privacy-policy.md").read_text(encoding="utf-8")
        self.assertIn("není souhlasem se zasíláním obchodních sdělení", t)
        self.assertIn("Žádost o hodnocení po nákupu", p)
        self.assertIn("neovlivňuje nákup", p)


if __name__ == "__main__":
    unittest.main()
