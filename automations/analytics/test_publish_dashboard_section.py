#!/usr/bin/env python3
"""
Publishing one level deeper: `--section growth`.

The weekly dashboard publishes to `reports/molosoc/index.html`. The TrafficDom
Growth report publishes to `reports/molosoc/growth/index.html`, through this
same publisher, over the same connection, with the same guards — deliberately,
rather than through a second publisher that would have to re-earn all of them.

Only the section is new, so only the section is tested here. What that means in
practice is one question asked several ways: **can a run asked for `growth` ever
land on `molosoc`?** That directory holds the live Analytics report, and writing
`index.html` into it would replace a working client-facing page with a different
one.

The answer has to be no at three separate points, and each is tested:

  * the derivation appends the section and cannot substitute it;
  * the path check refuses a destination whose tail is wrong — including a
    destination that is exactly the Analytics directory;
  * the server's own working directory is compared before anything is sent, so
    a chroot or a symlink that lands the run one level up aborts it.

Everything runs offline: no network, no credentials, no SFTP server.

Run with:  python3 -m pytest automations/analytics/
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import publish_dashboard as pub  # noqa: E402
from test_dashboard import FakeSFTP  # noqa: E402

BASE = "/public_html/Trafficdom.com/reports"
ANALYTICS_DIR = f"{BASE}/molosoc"
GROWTH_DIR = f"{BASE}/molosoc/growth"


# --------------------------------------------------------------------------
# The section is a closed set, not a path
# --------------------------------------------------------------------------

def test_growth_is_the_only_section_there_is():
    assert pub.ALLOWED_SECTIONS == ("growth",)


def test_the_section_appears_in_the_cli_as_a_fixed_choice():
    """Rejected by the parser, before any path exists to be checked."""
    with pytest.raises(SystemExit):
        pub.parse_args(["--section", "molosoc"])
    assert pub.parse_args(["--section", "growth"]).section == "growth"
    assert pub.parse_args([]).section is None


def test_an_unknown_section_is_refused_by_the_derivation_too(): 
    """Not only by argparse: the function is callable from other code."""
    for bad in ("molosoc", "..", "../molosoc", "growth/", "", "GROWTH"):
        with pytest.raises(pub.PublishError):
            pub.resolve_remote_dir(BASE, bad)


# --------------------------------------------------------------------------
# The destination is appended, never substituted
# --------------------------------------------------------------------------

def test_the_growth_destination_sits_inside_the_analytics_one():
    assert pub.resolve_remote_dir(BASE, "growth") == GROWTH_DIR
    assert GROWTH_DIR.startswith(ANALYTICS_DIR + "/")


def test_the_dashboard_destination_is_unchanged():
    """The existing weekly publish must behave exactly as it did before."""
    assert pub.resolve_remote_dir(BASE) == ANALYTICS_DIR
    assert pub.resolve_remote_dir(BASE, None) == ANALYTICS_DIR


def test_the_remote_file_is_still_only_index_html():
    assert pub.REMOTE_FILENAME == "index.html"


def test_the_public_url_is_derived_from_the_same_rule():
    assert pub.public_url() == "https://trafficdom.com/reports/molosoc/"
    assert pub.public_url("growth") == "https://trafficdom.com/reports/molosoc/growth/"


# --------------------------------------------------------------------------
# A sectioned run may not land on the Analytics report
# --------------------------------------------------------------------------

def test_the_analytics_directory_is_refused_when_a_section_was_asked_for():
    """The whole point: with --section growth, `.../molosoc` is a wrong path."""
    with pytest.raises(pub.PublishError) as excinfo:
        pub.check_remote_dir(ANALYTICS_DIR, BASE, "growth")
    assert "molosoc/growth" in str(excinfo.value)


def test_a_path_that_escapes_the_base_is_refused_with_a_section_too():
    with pytest.raises(pub.PublishError):
        pub.check_remote_dir("/elsewhere/molosoc/growth", BASE, "growth")


def test_relative_segments_are_refused_with_a_section_too():
    with pytest.raises(pub.PublishError):
        pub.check_remote_dir(f"{BASE}/molosoc/../molosoc/growth", BASE, "growth")


def test_a_wordpress_directory_is_refused_with_a_section_too():
    with pytest.raises(pub.PublishError):
        pub.check_remote_dir(f"{BASE}/wp-content/molosoc/growth", BASE, "growth")


def test_the_growth_path_still_ends_in_the_project_directory_lineage():
    resolved = pub.resolve_remote_dir(BASE, "growth")
    assert resolved.split("/")[-2:] == ["molosoc", "growth"]


# --------------------------------------------------------------------------
# The server's opinion of where we are is what decides
# --------------------------------------------------------------------------

def test_the_upload_is_abandoned_if_the_server_puts_us_in_the_analytics_dir():
    """A chroot or symlink landing one level up must abort, not overwrite."""
    sftp = FakeSFTP(cwd=ANALYTICS_DIR)

    with pytest.raises(pub.PublishError) as excinfo:
        pub.verify_location(sftp, GROWTH_DIR, "growth")

    assert "FAILED" in str(excinfo.value)
    assert "Nothing was uploaded" in str(excinfo.value)
    assert not sftp.stored


def test_the_location_check_passes_on_the_growth_directory():
    sftp = FakeSFTP(cwd=GROWTH_DIR)
    assert pub.verify_location(sftp, GROWTH_DIR, "growth") == GROWTH_DIR


def test_a_chrooted_account_reporting_the_tail_is_accepted():
    sftp = FakeSFTP(cwd="/molosoc/growth")
    assert pub.verify_location(sftp, GROWTH_DIR, "growth") == "/molosoc/growth"


def test_a_chrooted_account_reporting_only_molosoc_is_not():
    sftp = FakeSFTP(cwd="/molosoc")
    with pytest.raises(pub.PublishError):
        pub.verify_location(sftp, GROWTH_DIR, "growth")


# --------------------------------------------------------------------------
# Only the last segment is ever created
# --------------------------------------------------------------------------

def test_growth_is_created_inside_an_existing_molosoc_directory():
    """`molosoc/` must already exist; only `growth/` may be made."""
    sftp = FakeSFTP(cwd="/", dirs={ANALYTICS_DIR})
    entered = pub.enter_remote_dir(sftp, GROWTH_DIR, section="growth")
    assert entered == GROWTH_DIR
    assert sftp.made == [GROWTH_DIR]


def test_a_missing_molosoc_directory_is_an_error_not_something_to_build():
    sftp = FakeSFTP(cwd="/", dirs=set())
    with pytest.raises(pub.PublishError):
        pub.enter_remote_dir(sftp, GROWTH_DIR, section="growth")
    assert sftp.made == []


def test_an_existing_growth_directory_is_entered_rather_than_recreated():
    sftp = FakeSFTP(cwd="/", dirs={ANALYTICS_DIR, GROWTH_DIR})
    assert pub.enter_remote_dir(sftp, GROWTH_DIR, section="growth") == GROWTH_DIR
    assert sftp.made == []


def test_nothing_is_ever_deleted_or_renamed():
    """The publisher has no such capability; asserted rather than assumed."""
    source = Path(pub.__file__).read_text(encoding="utf-8")
    body = "\n".join(line for line in source.splitlines()
                     if not line.lstrip().startswith("#"))
    for forbidden in ("sftp.remove", "sftp.unlink", "sftp.rmdir", "sftp.rename",
                      "sftp.posix_rename", "sftp.symlink", "sftp.truncate"):
        assert forbidden not in body


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
