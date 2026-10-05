"""Issue #99 Test 1: preconnect hints only on the foot-cover landing page."""
import re
import shutil
import subprocess
import textwrap
import unittest
from pathlib import Path

FUNCTIONS = Path(__file__).resolve().parents[1] / "site/theme/functions.php"


def _function_source():
    src = FUNCTIONS.read_text(encoding="utf-8")
    start = src.index("function molosoc_landing_preconnect_hints()")
    end = src.index("add_action( 'wp_head', function () {", start)
    hook_end = src.index("}, 1 );", end) + len("}, 1 );")
    return src[start:hook_end]


@unittest.skipUnless(shutil.which("php"), "php not installed")
class LandingPreconnectHints(unittest.TestCase):
    def render(self, slug):
        harness = textwrap.dedent(
            """<?php
            $GLOBALS['hooks'] = array();
            $slug = %s;
            function is_page( $slugs ) { global $slug; return in_array( $slug, (array) $slugs, true ); }
            function esc_url( $u ) { return $u; }
            function add_action( $tag, $cb, $prio = 10 ) { $GLOBALS['hooks'][] = array( $tag, $cb, $prio ); }
            %s
            foreach ( $GLOBALS['hooks'] as $h ) { if ( 'wp_head' === $h[0] ) { call_user_func( $h[1] ); } }
            """
        ) % (repr(slug).replace('"', "'"), _function_source())
        out = subprocess.run(
            ["php"], input=harness, capture_output=True, text=True, check=True
        )
        return out.stdout

    def test_landing_pages_get_exactly_three_preconnects(self):
        for slug in ("moisture-lock-foot-cover", "hydratacni-navlek-na-nohy"):
            out = self.render(slug)
            self.assertEqual(
                re.findall(r'<link rel="preconnect" href="([^"]+)"', out),
                ["https://unpkg.com", "https://fonts.googleapis.com", "https://fonts.gstatic.com"],
            )
            self.assertIn('<link rel="preconnect" href="https://unpkg.com" crossorigin>', out)
            self.assertIn('<link rel="preconnect" href="https://fonts.googleapis.com">', out)
            self.assertIn('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>', out)
            self.assertNotIn("preload", out)

    def test_other_pages_get_nothing(self):
        for slug in ("cracked-heels", "home", "navleky-na-nohy"):
            self.assertEqual(self.render(slug), "")

    def test_hook_runs_early_in_wp_head(self):
        src = FUNCTIONS.read_text(encoding="utf-8")
        self.assertIn("}, 1 );", _function_source())
        self.assertEqual(src.count("function molosoc_landing_preconnect_hints"), 1)


if __name__ == "__main__":
    unittest.main()
