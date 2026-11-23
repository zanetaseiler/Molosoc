"""Issue #382: Black Friday top bar until Mon 30 Nov 2026 23:59 Prague, then the
Christmas bar again; Black Friday pages show the end date and 302 to the
Christmas pages after it; "Dobírka:" label visible on the dark BF hero; Czech
pages show Czech reviews only.

Three layers, all with a FAKED clock:
- PHP (server render) through tests/fixtures/bf_bar_stub_382.php — needs the php CLI, skipped without it;
- the inline client-side scripts (what a page cached before the switch runs) executed in Node with a fake Date.now;
- static checks of the source.
"""
import json
import re
import shutil
import subprocess
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
STUB = REPO / "tests/fixtures/bf_bar_stub_382.php"
BAR = (ROOT / "inc/xmas-bar.php").read_text(encoding="utf-8")
BF = (ROOT / "inc/landing-bf.php").read_text(encoding="utf-8")
BF_CSS = (ROOT / "assets/css/landing-bf.css").read_text(encoding="utf-8")
BAR_CSS = (ROOT / "assets/css/xmas-bar.css").read_text(encoding="utf-8")
REVIEWS = (ROOT / "inc/real-reviews.php").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")

END = int(datetime(2026, 12, 1, 0, 0, tzinfo=ZoneInfo("Europe/Prague")).timestamp())  # 1796079600
DURING = END - 1  # Mon 30 Nov 2026 23:59:59 Prague
AFTER = END  # Tue 1 Dec 2026 00:00:00 Prague
TODAY = int(datetime(2026, 11, 24, 10, 0, tzinfo=ZoneInfo("Europe/Prague")).timestamp())

CZ_BF = "Black Friday — první pár 209 Kč, každý další 199 Kč. Platí do pondělí 30. 11."
EN_BF = "Black Friday — first pair 209 CZK, each extra pair 199 CZK. Until Monday 30 Nov"
CZ_XMAS = "🎄 Tip na vánoční dárek — Objevte vánoční nabídku MOLOSOC"
EN_XMAS = "🎄 Christmas Gift Idea — Discover the MOLOSOC Holiday Offer"


def php(*args):
    if not shutil.which("php"):
        raise unittest.SkipTest("no php")
    return subprocess.run(["php", str(STUB), *map(str, args)], capture_output=True, text=True, check=True).stdout


def node(src):
    if not shutil.which("node"):
        raise unittest.SkipTest("no node")
    return subprocess.run(["node", "-e", src], capture_output=True, text=True, check=True).stdout


class EndTime(unittest.TestCase):
    def test_end_is_1_dec_midnight_prague(self):
        self.assertEqual(END, 1796079600)
        self.assertIn("new DateTimeImmutable( '2026-12-01 00:00:00', new DateTimeZone( 'Europe/Prague' ) )", BF)
        self.assertIn("apply_filters( 'molosoc_bf_now', time() )", BF)
        self.assertIn("return molosoc_bf_now() < molosoc_bf_end_ts();", BF)


# ---------- server render (php CLI) ----------

class ServerBar(unittest.TestCase):
    def test_bf_bar_until_the_end(self):
        for now in (TODAY, DURING):
            cz = php("bar", "cz", now)
            self.assertIn(CZ_BF, cz)
            self.assertIn('href="https://example.test/cz/black-friday-molosoc/"', cz)
            self.assertNotIn("🎄", cz.split("<script>")[0])
            self.assertIn('"molosocBfBar382"', cz)
            en = php("bar", "en", now)
            self.assertIn(EN_BF, en)
            self.assertIn('href="https://example.test/black-friday-offer-molosoc/"', en)

    def test_christmas_bar_from_1_dec(self):
        cz = php("bar", "cz", AFTER)
        self.assertIn(CZ_XMAS, cz)
        self.assertIn('href="https://example.test/cz/vanocni-darek-molosoc/"', cz)
        self.assertNotIn("Black Friday", cz)
        self.assertIn('"molosocXmasBar317"', cz)
        en = php("bar", "en", AFTER)
        self.assertIn(EN_XMAS, en)
        self.assertIn('href="https://example.test/christmas-gift-molosoc/"', en)

    def test_unpublished_bf_page_keeps_the_christmas_bar(self):
        self.assertIn(CZ_XMAS, php("bar", "cz", TODAY, "bf-draft"))

    def test_bar_hidden_on_bf_pages_through_the_landing_family_gate(self):
        self.assertIn("molosoc_is_xmas_landing() ) {\n\t\treturn array();", BAR)


class ServerRedirect(unittest.TestCase):
    def test_no_redirect_during_black_friday(self):
        for lang in ("cz", "en"):
            self.assertEqual(php("redirect", lang, DURING).strip(), "")

    def test_302_to_christmas_after_the_end_with_query_kept(self):
        self.assertEqual(php("redirect", "cz", AFTER, "", "utm_source=meta&fbclid=x").strip(),
                         "REDIRECT 302 https://example.test/cz/vanocni-darek-molosoc/?utm_source=meta&fbclid=x")
        self.assertEqual(php("redirect", "en", AFTER).strip(), "REDIRECT 302 https://example.test/christmas-gift-molosoc/")

    def test_other_pages_never_redirect(self):
        self.assertEqual(php("redirect", "cz", AFTER, "", "", "vanocni-darek-molosoc").strip(), "")

    def test_guard_script(self):
        out = php("guard", "cz", TODAY)
        self.assertIn("Date.now()>=%d000" % END, out)
        self.assertIn('"https:\\/\\/example.test\\/cz\\/vanocni-darek-molosoc\\/"', out)


# ---------- client side: a copy cached BEFORE the switch, run with a fake clock ----------

def bar_script():
    m = re.search(r"<script>\n(\(function\(\)\{var b=document.getElementById\(\"molosoc-xmas-bar\"\).*?)\n</script>", BAR, re.S)
    return m.group(1)


def run_bar(now_ms, key, swap, stored=None):
    js = bar_script()
    js = js.replace("<?php echo wp_json_encode( $d['key'] ); ?>", json.dumps(key))
    js = js.replace("<?php echo wp_json_encode( $swap ); ?>", json.dumps(swap, ensure_ascii=False))
    assert "<?php" not in js, js
    harness = """
const store = %s;
const link = {href: 'https://example.test/cz/black-friday-molosoc/'};
const text = {textContent: %s};
const close = {addEventListener(){}};
const bar = {hidden: false, attrs: {}, setAttribute(k, v){ this.attrs[k] = v; },
  querySelector(s){ return s.endsWith('__link') ? link : s.endsWith('__text') ? text : close; }};
global.document = {getElementById(){ return bar; }};
global.window = {sessionStorage: {getItem(k){ return store[k] || null; }, setItem(k, v){ store[k] = v; }}};
Date.now = () => %d;
%s
console.log(JSON.stringify({hidden: bar.hidden, href: link.href, text: text.textContent, label: bar.attrs['aria-label'] || null}));
""" % (json.dumps(stored or {}), json.dumps(CZ_BF, ensure_ascii=False), now_ms, js)
    return json.loads(node(harness))


SWAP = {"end": END * 1000, "url": "https://example.test/cz/vanocni-darek-molosoc/", "text": CZ_XMAS, "label": "Vánoční nabídka", "key": "molosocXmasBar317"}


class ClientBar(unittest.TestCase):
    def test_cached_bf_bar_stays_bf_until_2359(self):
        r = run_bar(DURING * 1000 + 999, "molosocBfBar382", SWAP)
        self.assertEqual((r["hidden"], r["text"]), (False, CZ_BF))
        self.assertEqual(r["href"], "https://example.test/cz/black-friday-molosoc/")

    def test_cached_bf_bar_turns_into_the_christmas_bar_at_midnight(self):
        r = run_bar(AFTER * 1000, "molosocBfBar382", SWAP)
        self.assertEqual(r, {"hidden": False, "href": SWAP["url"], "text": CZ_XMAS, "label": "Vánoční nabídka"})

    def test_fresh_key_closed_christmas_bar_does_not_hide_bf(self):
        r = run_bar(TODAY * 1000, "molosocBfBar382", SWAP, {"molosocXmasBar317": "1"})
        self.assertFalse(r["hidden"])
        self.assertTrue(run_bar(TODAY * 1000, "molosocBfBar382", SWAP, {"molosocBfBar382": "1"})["hidden"])

    def test_after_switch_the_christmas_dismissal_applies(self):
        self.assertTrue(run_bar(AFTER * 1000, "molosocBfBar382", SWAP, {"molosocXmasBar317": "1"})["hidden"])

    def test_no_christmas_page_means_hide_after_the_end(self):
        empty = {"end": END * 1000, "url": "", "text": "", "label": "", "key": ""}
        self.assertTrue(run_bar(AFTER * 1000, "molosocBfBar382", empty)["hidden"])

    def test_plain_christmas_bar_is_untouched(self):
        r = run_bar(AFTER * 1000, "molosocXmasBar317", None)
        self.assertEqual((r["hidden"], r["text"]), (False, CZ_BF))  # harness text: no swap happens


class ClientGuard(unittest.TestCase):
    def run_guard(self, now_ms):
        m = re.search(r"'(<script>\(function\(\)\{if\(Date\.now\(\)>=%d\)\{location\.replace\(%s\+location\.search\+location\.hash\);\}\}\)\(\);</script>)'", BF)
        js = m.group(1)[len("<script>"):-len("</script>")]
        js = js.replace("%d", str(END * 1000)).replace("%s", json.dumps("https://example.test/cz/vanocni-darek-molosoc/"))
        return node("""let went=null; global.location={search:'?utm_source=meta',hash:'#lpx-bundle',replace(u){went=u;}};
Date.now=()=>%d; %s; console.log(JSON.stringify(went));""" % (now_ms, js)).strip()

    def test_cached_bf_page_stays_until_2359(self):
        self.assertEqual(self.run_guard(DURING * 1000 + 999), "null")

    def test_cached_bf_page_leaves_for_christmas_at_midnight(self):
        self.assertEqual(self.run_guard(AFTER * 1000), json.dumps("https://example.test/cz/vanocni-darek-molosoc/?utm_source=meta#lpx-bundle"))


# ---------- page copy, styles, reviews ----------

class PageCopy(unittest.TestCase):
    def test_end_date_wording(self):
        self.assertIn("'Nabídka platí do pondělí 30. 11.'", BF)
        self.assertIn("'Offer valid until Monday 30 Nov.'", BF)
        self.assertIn("'Platí do pondělí 30. 11.'", BF)
        self.assertIn("'Until Monday 30 Nov'", BF)
        self.assertEqual(BF.count("'deadline'   => molosoc_bf_until_text( '"), 2)

    def test_redirect_hooked_and_uncached(self):
        self.assertIn("add_action( 'template_redirect', 'molosoc_bf_expired_redirect', 1 );", BF)
        self.assertIn("define( 'DONOTCACHEPAGE', true );", BF)
        self.assertIn("wp_safe_redirect( $url, 302, 'MOLOSOC' );", BF)
        self.assertIn("add_action( 'wp_head', 'molosoc_bf_expired_guard', 0 );", BF)

    def test_cod_label_and_end_date_visible_on_the_dark_hero(self):
        self.assertIn(".lpx--bf .lpx-hero .lpb-cod strong { color: var(--bf-cream); }", BF_CSS)
        self.assertIn(".lpx--bf .lpx-hero .lpx-deadline { color: var(--bf-gold); }", BF_CSS)

    def test_bar_look_unchanged_and_version_bumped(self):
        self.assertNotIn("black", BAR_CSS.lower())
        self.assertIn("Version: 0.2.127", STYLE)


class CzechReviews(unittest.TestCase):
    def czech(self, text):
        return re.search(r"[ěščřžůťďňĚŠČŘŽŮŤĎŇ]", text) is not None

    def test_live_reviews_split(self):
        self.assertTrue(self.czech("Ahoj, funguje velmi dobře, včera jsem ho vyzkoušela"))
        self.assertFalse(self.czech("MUY PRACTICAS EL RESULTADO ES INMEDIATO Y CON EL USO FRECUENTE NOTAS LA DIFERENCIAA, DURABLES"))
        self.assertFalse(self.czech("Realmente me sorprendieron mi podologo se sorprendio de la suabidad de mi pie, altamente recomendabes"))

    def test_php_uses_the_same_pattern_for_cz_only(self):
        self.assertIn("preg_match( '/[ěščřžůťďňĚŠČŘŽŮŤĎŇ]/u'", REVIEWS)
        self.assertIn("if ( 'cz' === $lang ) {", REVIEWS)
        self.assertIn("molosoc_real_reviews_is_czech( $c->comment_content )", REVIEWS)


if __name__ == "__main__":
    unittest.main()
