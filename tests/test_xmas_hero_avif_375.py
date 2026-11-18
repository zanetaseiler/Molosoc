"""Issue #375 follow-up (brief of 18 Nov 2026): mobile LCP without cropping.

The Christmas hero gets AVIF copies of the same full 3:2 frame (480/768/1080 and
the 1536 px "<base>.avif"), served through <picture><source type="image/avif">
with the WebP <img> as fallback, and a type="image/avif" preload. Also covers
the shipping copy 69 -> 79 Kč (PPL box at 69 Kč is no longer offered at checkout).
"""
import re
import struct
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
THEME = REPO / "site/theme"
IMG = THEME / "assets/images/landing-xmas"
INC = (THEME / "inc/landing-xmas.php").read_text(encoding="utf-8")
CSS = (THEME / "assets/css/landing-xmas.css").read_text(encoding="utf-8")


def avif_size(path):
    """Width/height from the AVIF 'ispe' box (no image library needed)."""
    data = path.read_bytes()
    i = data.find(b"ispe")
    assert i > 0, path
    return struct.unpack(">II", data[i + 8:i + 16])


def webp_size(path):
    data = path.read_bytes()
    kind = data[12:16]
    if kind == b"VP8 ":
        w, h = struct.unpack("<HH", data[26:30])
        return w & 0x3FFF, h & 0x3FFF
    if kind == b"VP8L":
        b = data[21:25]
        return 1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
    if kind == b"VP8X":
        return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
    raise AssertionError(kind)


def block(src, start, end):
    i = src.index(start)
    return src[i:src.index(end, i)]


class HeroAvifFiles(unittest.TestCase):
    def test_full_frame_avif_at_every_width(self):
        ow, oh = webp_size(IMG / "MOLOSOC_Christmas_Gift_Scene_01.webp")
        self.assertEqual((ow, oh), (1536, 1024))
        expected = {"-480": 480, "-768": 768, "-1080": 1080, "": 1536}
        for suffix, w in expected.items():
            p = IMG / f"MOLOSOC_Christmas_Gift_Scene_01{suffix}.avif"
            self.assertTrue(p.exists(), p.name)
            aw, ah = avif_size(p)
            self.assertEqual(aw, w, p.name)
            # Same 3:2 frame as the upload: scaled, never cropped.
            self.assertAlmostEqual(aw / ah, ow / oh, places=2, msg=p.name)

    def test_avif_is_lighter_than_the_webp_it_replaces(self):
        for suffix in ("-480", "-768", "-1080", ""):
            a = (IMG / f"MOLOSOC_Christmas_Gift_Scene_01{suffix}.avif").stat().st_size
            w = (IMG / f"MOLOSOC_Christmas_Gift_Scene_01{suffix}.webp").stat().st_size
            self.assertLess(a, w, suffix)


class HeroAvifMarkup(unittest.TestCase):
    def test_avif_srcset_needs_every_file(self):
        fn = block(INC, "function molosoc_xmas_avif_srcset( $key )", "\n}")
        self.assertIn("foreach ( molosoc_xmas_image_widths() as $w )", fn)
        self.assertIn("$files[ $base . '.avif' ]", fn)
        self.assertIn("if ( ! file_exists( $dir . $file ) ) {\n\t\t\treturn '';", fn)
        self.assertIn("'?v=' . molosoc_xmas_image_rev()", fn)

    def test_picture_wraps_the_unchanged_img(self):
        fn = block(INC, "function molosoc_xmas_image( $key, $alt, $attrs = '' )", "\n}")
        self.assertIn("'<img src=\"%s\" srcset=\"%s\" sizes=\"%s\" alt=\"%s\"%s decoding=\"async\" %s>'", fn)
        self.assertIn("'<picture><source type=\"image/avif\" srcset=\"%s\" sizes=\"%s\">%s</picture>'", fn)
        self.assertIn("esc_attr( $set['sizes'] )", fn)
        self.assertIn("return $img;", fn)

    def test_preload_matches_the_avif_source(self):
        fn = block(INC, "function molosoc_xmas_head()", "\n}")
        self.assertIn("molosoc_xmas_avif_srcset( 'scene-01' )", fn)
        self.assertIn('<link rel="preload" as="image" type="image/avif" fetchpriority="high" imagesrcset="%s" imagesizes="%s">', fn)
        # The WebP preload stays as the fallback when the AVIF set is incomplete.
        self.assertIn('<link rel="preload" as="image" fetchpriority="high" href="%s" imagesrcset="%s" imagesizes="%s">', fn)

    def test_no_crop_in_css(self):
        self.assertIn(".lpx-hero__media picture { display: block; }", CSS)
        hero = "\n".join(l for l in CSS.splitlines() if "lpx-hero__media" in l)
        for bad in ("object-fit", "aspect-ratio", "max-height", "height: 1", "height:1"):
            self.assertNotIn(bad, hero)


class ShippingFrom79(unittest.TestCase):
    def test_no_69_shipping_claim_left_in_the_theme(self):
        hits = []
        for p in THEME.rglob("*.php"):
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                code = line.strip()
                if code.startswith(("*", "//", "/*", "<?php /*")):
                    continue  # history in comments, not copy
                if re.search(r"\b69 ?(Kč|CZK)", code):
                    hits.append(f"{p.relative_to(THEME)}:{n}")
        self.assertEqual(hits, [])

    def test_every_source_says_79(self):
        self.assertIn("'ship_from' => 79,", INC)
        self.assertIn("'Doprava od 79 Kč' : 'Shipping from 79 CZK'", (THEME / "inc/woocommerce-lang.php").read_text(encoding="utf-8"))
        self.assertIn("$lpb_shipping    = 'Doprava od 79 Kč';", (THEME / "page-hydratacni-navleky-molosoc.php").read_text(encoding="utf-8"))
        self.assertIn("$lpb_shipping = 'Shipping from 79 CZK';", (THEME / "page-hydrating-foot-covers-molosoc.php").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
