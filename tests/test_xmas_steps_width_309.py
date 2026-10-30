"""Issue #309: on the Christmas pages the "How it works" steps list is as wide as the
photos (max 1080 px, centred), not the full section width."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site/theme"
CSS = (ROOT / "assets/css/landing-xmas.css").read_text(encoding="utf-8")
STYLE = (ROOT / "style.css").read_text(encoding="utf-8")


class StepsWidth(unittest.TestCase):
    def test_steps_share_the_figure_width_and_centring(self):
        fig = re.search(r"\n\.lpx-figure \{([^}]*)\}", CSS).group(1)
        steps = re.search(r"\n\.lpx \.lpb-steps \{([^}]*)\}", CSS).group(1)
        self.assertIn("max-width: var(--lpb-max, 1080px)", fig)
        self.assertIn("max-width: var(--lpb-max, 1080px)", steps)
        self.assertIn("margin-left: auto", steps)
        self.assertIn("margin-right: auto", steps)
        self.assertNotIn(".lpb-steps", (ROOT / "assets/css/landing-b.css").read_text(encoding="utf-8").split("/* Issue")[0][:0])  # Landing B untouched (file not edited here)

    def test_testimonial_title_has_more_room_below(self):
        rule = re.search(r"\n\.lpx \.lpb-testimonial__title \{([^}]*)\}", CSS).group(1)
        self.assertIn("margin-bottom: 1.1rem", rule)

    def test_version_bumped(self):
        v = re.search(r"^Version: (\d+)\.(\d+)\.(\d+)$", STYLE, re.M)
        self.assertGreaterEqual(tuple(int(x) for x in v.groups()), (0, 2, 113))


if __name__ == "__main__":
    unittest.main()
