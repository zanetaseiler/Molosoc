"""Issue #393: every site/mu-plugins/*.php must load together in ONE PHP process.

WordPress loads every mu-plugin unconditionally, so a function or constant declared in two
mu-plugins is a site-wide fatal (PR #392: `molosoc_lp_gate()` in both the PPL and the label
preview mu-plugin took molosoc.com down with HTTP 500). The per-feature tests each load only
their own subset of files and could not see it.

Two independent guards:
1. Static: no top-level function name or `const`/`define()` constant name is declared in more
   than one mu-plugin (case-insensitive for functions, as PHP is).
2. Runtime: `php` requires all mu-plugins together (minimal WP stubs, no network/DB/mail), with
   the feature constants OFF and again with the registration-gating constants ON, and fails on
   any fatal, warning, notice or output.
Plus a proof that the runtime guard catches the #392 bug (the pre-fix PPL file from git).
"""
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MU = ROOT / "site/mu-plugins"
HAVE_PHP = shutil.which("php") is not None

FUNC_RE = re.compile(r"^(?:\s*)function\s+&?\s*([A-Za-z_]\w*)\s*\(", re.M)
CONST_RE = re.compile(r"^\s*const\s+([A-Za-z_]\w*)\s*=", re.M)
DEFINE_RE = re.compile(r"""\bdefine\s*\(\s*['"]([A-Za-z_]\w*)['"]""")

# Constants a mu-plugin may define only when wp-config has not (guarded by `! defined`), or
# WordPress core constants: defining them twice is not a redeclare of a mu-plugin symbol.
GUARDED_DEFINES = {"DONOTCACHEPAGE", "MOLOSOC_CZ_HOME_POLYLANG_SLUG"}

STUBS = r"""
error_reporting(E_ALL);
set_error_handler(function($no,$str,$file,$line){ fwrite(STDERR,"PHPERR $no $str $file:$line\n"); exit(3); });
define('ABSPATH','/x/');
$GLOBALS['__hooks'] = array();
function add_action($h,$cb=null,$p=10,$a=1){ $GLOBALS['__hooks'][] = is_string($h) ? $h : '?'; return true; }
function add_filter($h,$cb=null,$p=10,$a=1){ $GLOBALS['__hooks'][] = is_string($h) ? $h : '?'; return true; }
function wp_get_environment_type(){ return 'production'; }
"""

# Registration-gating constants (see `defined( 'MOLOSOC_...' )` at the bottom of each file).
ON_CONSTANTS = {
    "MOLOSOC_LABEL_AUTO_ENABLED": True,
    "MOLOSOC_LABEL_AUTO_PREVIEW": True,
    "MOLOSOC_LABEL_AUTO_PPL_ENABLED": True,
    "MOLOSOC_LABEL_AUTO_PPL_LIMIT": 1,
    "MOLOSOC_LABEL_DELIVERY_ENABLED": True,
    "MOLOSOC_LABEL_DISPATCH_DRY_RUN": True,
    "MOLOSOC_LABEL_LIVE_ENABLED": True,
    "MOLOSOC_LABEL_LIVE_PREVIEW": True,
    "MOLOSOC_TEST_MAIL_366_ENABLED": True,
}


def mu_files():
    return sorted(MU.glob("*.php"))


def strip_comments(src):
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"(?m)(^|\s)(//|#).*$", r"\1", src)


def declarations(path):
    src = strip_comments(path.read_text(encoding="utf-8"))
    # Only PHP code (skip inline <script> blocks emitted between ?> and <?php).
    src = re.sub(r"\?>.*?(<\?php|\Z)", "", src, flags=re.S)
    funcs = [m.group(1) for m in FUNC_RE.finditer(src)]
    consts = [m.group(1) for m in CONST_RE.finditer(src)]
    defines = [m.group(1) for m in DEFINE_RE.finditer(src) if m.group(1) not in GUARDED_DEFINES]
    return funcs, consts + defines


def load_all(files, consts=None):
    pre = STUBS
    for k, v in (consts or {}).items():
        pre += "define(%s, %s);\n" % (json.dumps(k), json.dumps(v))
    body = "".join("require %s;\n" % json.dumps(str(f)) for f in files)
    code = pre + body + "echo 'LOADED ' . count($GLOBALS['__hooks']);\n"
    with tempfile.NamedTemporaryFile("w", suffix=".php", delete=False) as fh:
        fh.write("<?php\n" + code)
        script = fh.name
    try:
        return subprocess.run(["php", "-d", "display_errors=stderr", "-d", "log_errors=0", script],
                              capture_output=True, text=True)
    finally:
        Path(script).unlink()


class StaticUniqueness(unittest.TestCase):
    def test_mu_plugins_present(self):
        names = {f.name for f in mu_files()}
        self.assertIn("molosoc-carrier-label-ppl.php", names)
        self.assertIn("molosoc-carrier-label-preview.php", names)

    def test_no_duplicate_function_names(self):
        seen = {}
        for f in mu_files():
            funcs, _ = declarations(f)
            for name in funcs:
                seen.setdefault(name.lower(), []).append(f.name)
        dupes = {k: v for k, v in seen.items() if len(v) > 1}
        self.assertEqual(dupes, {}, "function declared more than once across mu-plugins")

    def test_no_duplicate_constant_names(self):
        seen = {}
        for f in mu_files():
            _, consts = declarations(f)
            for name in consts:
                seen.setdefault(name, []).append(f.name)
        dupes = {k: v for k, v in seen.items() if len(v) > 1}
        self.assertEqual(dupes, {}, "constant declared more than once across mu-plugins")

    def test_ppl_uses_own_prefix(self):
        funcs, consts = declarations(MU / "molosoc-carrier-label-ppl.php")
        self.assertTrue(funcs and consts)
        self.assertEqual([n for n in funcs if not n.startswith("molosoc_lppl_")], [])
        self.assertEqual([n for n in consts if not n.startswith("MOLOSOC_LPPL_")], [])

    def test_static_check_detects_the_392_collision(self):
        src = (MU / "molosoc-carrier-label-ppl.php").read_text(encoding="utf-8")
        old = re.sub(r"\bmolosoc_lppl_", "molosoc_lp_", src)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.php"
            p.write_text(old, encoding="utf-8")
            funcs_old, _ = declarations(p)
        funcs_preview, _ = declarations(MU / "molosoc-carrier-label-preview.php")
        self.assertIn("molosoc_lp_gate", set(funcs_old) & set(funcs_preview))


@unittest.skipUnless(HAVE_PHP, "php not installed")
class RuntimeLoadAll(unittest.TestCase):
    def assert_clean(self, r):
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertEqual(r.stderr, "")
        self.assertRegex(r.stdout, r"^LOADED \d+$")

    def test_all_mu_plugins_load_together_defaults_off(self):
        r = load_all(mu_files())
        self.assert_clean(r)

    def test_all_mu_plugins_load_together_constants_on(self):
        r = load_all(mu_files(), ON_CONSTANTS)
        self.assert_clean(r)
        self.assertGreater(int(r.stdout.split()[1]), 0)

    def test_all_mu_plugins_load_in_reverse_order(self):
        self.assert_clean(load_all(list(reversed(mu_files())), ON_CONSTANTS))

    def test_runtime_check_detects_the_392_fatal(self):
        # The exact PPL file shipped by #392 (merge 2072c92), next to today's preview file.
        old = subprocess.run(["git", "-C", str(ROOT), "show", "2072c92:site/mu-plugins/molosoc-carrier-label-ppl.php"],
                             capture_output=True, text=True)
        if old.returncode != 0:
            self.skipTest("git history for 2072c92 not available")
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "molosoc-carrier-label-ppl.php"
            bad.write_text(old.stdout, encoding="utf-8")
            files = [f for f in mu_files() if f.name not in ("molosoc-carrier-label-ppl.php", "molosoc-carrier-label-auto.php")]
            r = load_all(files + [bad])
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Cannot redeclare", r.stderr + r.stdout)
        self.assertIn("molosoc_lp_gate", r.stderr + r.stdout)


if __name__ == "__main__":
    unittest.main()
