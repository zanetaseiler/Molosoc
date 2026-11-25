"""Issue #388: the Black Friday first screen continues the Meta ad — headline, benefit
line, one gold price line (amounts from the checkout price list), and a short silent
clip that never becomes the LCP element and is never requested before window load.
Rendering checks use the #378 stub (php CLI; skipped without php)."""
import re
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "site/theme"
BF = (ROOT / "inc/landing-bf.php").read_text(encoding="utf-8")
PART = (ROOT / "template-parts/landing-xmas.php").read_text(encoding="utf-8")
CSS = (ROOT / "assets/css/landing-bf.css").read_text(encoding="utf-8")
CLIP = ROOT / "assets/video/molosoc-we-tried-it-720.mp4"
COPY = BF[BF.index("function molosoc_bf_copy"):BF.index("function molosoc_bf_meta")]
SCRIPT = BF[BF.index("function molosoc_bf_hero_clip_script"):BF.index("add_action( 'wp_footer', 'molosoc_bf_hero_clip_script'")]
PHONE = CSS[CSS.rindex("@media (max-width: 560px) {"):]

PAGES = {
    "cz": ("page-black-friday-molosoc.php", "black-friday-molosoc"),
    "en": ("page-black-friday-offer-molosoc.php", "black-friday-offer-molosoc"),
}
EXPECT = {
    "cz": (
        "Krém zůstane na noze. Vy se můžete hýbat.",
        "Nitrilové návleky MOLOSOC na opakované použití – namažete, nasadíte a za 20–30 minut máte hebká chodidla. Bez klouzání a bez mastných stop.",
        "Black Friday: první pár 209 Kč, každý další 199 Kč · 3 páry 607 Kč",
        "Nabídka platí do pondělí 30. 11.",
        "Doprava od 79 Kč",
        "Vyberte svůj set",
    ),
    "en": (
        "The cream stays on your feet. You can keep moving.",
        "Reusable nitrile MOLOSOC covers – apply cream, slip them on, and after 20–30 minutes your feet feel soft. No slipping, no greasy marks.",
        "Black Friday: first pair 209 CZK, each extra pair 199 CZK · 3 pairs 607 CZK",
        "Offer valid until Monday 30 Nov.",
        "Shipping from 79 CZK",
        "Choose your set",
    ),
}


def rule(css, sel):
    return css[css.index(sel):].split("{", 1)[1].split("}", 1)[0]


def render(tpl, slug):
    if not shutil.which("php"):
        raise unittest.SkipTest("no php")
    return subprocess.run(["php", str(REPO / "tests/fixtures/landing_bf_stub_378.php"), tpl, slug, "body"], capture_output=True, text=True, check=True, cwd=REPO).stdout


class Copy(unittest.TestCase):
    def test_headline_and_benefit_line_verbatim(self):
        for h1, sub, *_ in EXPECT.values():
            self.assertIn("'h1'         => '%s'" % h1, COPY)
            self.assertIn("'sub'        => '%s'" % sub, COPY)

    def test_price_line_reads_the_checkout_price_list(self):
        self.assertIn("'Black Friday: první pár %1$s, každý další %2$s · 3 páry %3$s', $first, $next, $three", COPY)
        self.assertIn("'Black Friday: first pair %1$s, each extra pair %2$s · 3 pairs %3$s', $first, $next, $three", COPY)
        self.assertIn("molosoc_bf_money( molosoc_xmas_bundle_total( 3 ), $lang )", COPY)

    def test_rendered_hero(self):
        for lang, page in PAGES.items():
            html = render(*page)
            hero = html[html.index('<section class="lpx-hero"'):html.index('id="lpx-bundle"')]
            h1, sub, price, until, ship, btn = EXPECT[lang]
            self.assertIn('<h1 class="lpx-hero__title">%s</h1>' % h1, hero)
            self.assertIn('<p class="lpb-hero__lede">%s</p>' % sub, hero)
            self.assertIn('<p class="lpx-bf-price" translate="no">%s</p>' % price, hero)
            self.assertIn('<p class="lpx-deadline">%s</p>' % until, hero)
            self.assertIn('<p class="lpb-price__meta">%s</p>' % ship, hero)
            self.assertIn('<a class="lpb-btn" href="#lpx-bundle">%s</a>' % btn, hero)
            self.assertEqual("Zaplatíte při převzetí zásilky" in hero, lang == "cz")
            self.assertEqual(hero.count("data-bf-clip "), 1)


class Clip(unittest.TestCase):
    def test_markup_is_muted_inline_looping_and_requests_nothing(self):
        tag = re.search(r"'<template data-bf-clip-tpl>(<video [^']*</video>)</template>'", BF).group(1)
        for attr in ("muted", "loop", "playsinline", 'preload="none"', "data-src="):
            self.assertIn(attr, tag)
        self.assertNotRegex(tag, r"\s(src|poster|autoplay|controls)\b")

    def test_started_after_load_with_the_ad_image_as_poster(self):
        self.assertIn("window.addEventListener('load', ready)", SCRIPT)
        self.assertIn("v = tpl.content.firstElementChild.cloneNode(true);", SCRIPT)
        self.assertIn("v.poster = img.currentSrc || img.src;", SCRIPT)
        for guard in ("prefers-reduced-motion: reduce", "c.saveData", "/2g/"):
            self.assertIn(guard, SCRIPT)

    def test_never_larger_than_the_image_and_taps_reach_the_link(self):
        css = rule(CSS, ".lpx--bf .lpx-bf-clip {")
        self.assertIn("inset: 1px;", css)
        self.assertIn("width: calc(100% - 2px);", css)
        self.assertIn("object-fit: contain;", css)
        self.assertIn("pointer-events: none;", css)
        self.assertIn("opacity: 0;", css)

    def test_pause_button_is_localized(self):
        for label in ("Pozastavit video", "Přehrát video", "Pause video", "Play video"):
            self.assertIn("'%s'" % label, COPY)

    def test_file_is_small_silent_and_starts_fast(self):
        data = CLIP.read_bytes()
        self.assertLess(len(data), 800_000)
        self.assertEqual(data[4:8], b"ftyp")
        self.assertLess(data.index(b"moov"), data.index(b"mdat"))  # faststart
        self.assertNotIn(b"soun", data[:data.index(b"mdat")])  # no audio track

    def test_black_friday_only(self):
        self.assertIn("$lpx_bf ? molosoc_bf_hero_clip( $t ) : ''", PART)
        self.assertIn("if ( ! molosoc_is_bf_landing() ) {", SCRIPT)
        self.assertIn("$lpx_bf ? $t['ship'] : $lpx_fmt( $lpx_prices[1] ) . ' · ' . $t['ship']", PART)


class Phone(unittest.TestCase):
    def test_benefit_line_button_and_cod_are_shown(self):
        self.assertIn("display: block;", rule(PHONE, ".lpx--bf .lpx-hero .lpb-hero__lede {"))
        self.assertIn("display: inline-flex;", rule(PHONE, ".lpx--bf .lpx-hero > .lpx-hero__inner > .lpx-hero__copy > .lpb-btn {"))
        self.assertIn("display: block;", rule(PHONE, ".lpx--bf .lpx-hero .lpb-cod { display"))

    def test_ad_keeps_its_size_and_the_price_line_is_gold(self):
        self.assertIn(".lpx--bf .lpx-hero__media { max-width: 264px;", PHONE)
        self.assertIn("color: var(--bf-gold);", rule(CSS, ".lpx--bf .lpx-bf-price {"))


if __name__ == "__main__":
    unittest.main()
