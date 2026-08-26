#!/usr/bin/env python3
"""
Publishing one level deeper, and one client wider.

The weekly dashboard publishes to `reports/molosoc/index.html`. The
TrafficDom Growth report publishes to `reports/molosoc/growth/index.html`,
and — since the client-first cutover — the Zoe Social report publishes to
`reports/zoe/social/index.html`, and the TrafficDom client directory page
publishes to `reports/index.html` itself. All four go through this same
publisher, over the same connection, with the same guards — deliberately,
rather than through a second publisher that would have to re-earn all of
them.

What that means in practice is one question asked several ways: **can a
run asked for one destination ever land on another one?** Growth must
never land on the Analytics report one level up; Zoe's report must never
land inside Molosoc's directory or vice versa; the directory page itself
must never land inside any one client's directory.

The answer has to be no at three separate points, and each is tested:

  * the derivation appends the client and section and cannot substitute
    either;
  * the path check refuses a destination whose tail is wrong — including a
    destination that is exactly a sibling client or section directory;
  * the server's own working directory is compared before anything is sent, so
    a chroot or a symlink that lands the run one level up aborts it.

Every existing caller that never passes `--client` must keep publishing to
`molosoc`, exactly as before this file supported more than one client —
tested explicitly, not just assumed from the default.

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
EMAIL_DIR = f"{BASE}/molosoc/email-marketing"
MOLOSOC_ANALYTICS_SECTION_DIR = f"{BASE}/molosoc/analytics"
ZOE_DIR = f"{BASE}/zoe"
ZOE_SOCIAL_DIR = f"{BASE}/zoe/social"


# --------------------------------------------------------------------------
# Backward compatibility: every existing caller never passes --client
# --------------------------------------------------------------------------

def test_the_default_client_is_still_molosoc():
    assert pub.PROJECT_DIR == "molosoc"
    assert pub.parse_args([]).client == "molosoc"


def test_omitting_client_resolves_exactly_as_before():
    assert pub.resolve_remote_dir(BASE) == ANALYTICS_DIR
    assert pub.resolve_remote_dir(BASE, "growth") == GROWTH_DIR
    assert pub.public_url() == "https://trafficdom.com/reports/molosoc/"
    assert pub.public_url("growth") == "https://trafficdom.com/reports/molosoc/growth/"


# --------------------------------------------------------------------------
# Clients and sections are closed sets, not a path
# --------------------------------------------------------------------------

def test_the_allowed_clients_are_exactly_molosoc_and_zoe():
    assert pub.ALLOWED_CLIENTS == ("molosoc", "zoe")


def test_the_allowed_sections_are_scoped_per_client():
    assert pub.ALLOWED_SECTIONS == {
        "molosoc": ("growth", "email-marketing", "analytics"),
        "zoe": ("social",),
    }


def test_the_client_appears_in_the_cli_as_a_fixed_choice():
    with pytest.raises(SystemExit):
        pub.parse_args(["--client", "someone-else"])
    assert pub.parse_args(["--client", "zoe"]).client == "zoe"


def test_a_section_valid_for_one_client_is_refused_for_another():
    """The parser-level choice is the union of every client's sections;
    the specific client/section pairing is checked one level deeper."""
    with pytest.raises(pub.PublishError):
        pub.expected_tail("growth", client="zoe")
    with pytest.raises(pub.PublishError):
        pub.expected_tail("social", client="molosoc")


def test_an_unknown_section_is_refused_by_the_derivation_too():
    """Not only by argparse: the function is callable from other code."""
    for bad in ("molosoc", "..", "../molosoc", "growth/", "", "GROWTH"):
        with pytest.raises(pub.PublishError):
            pub.resolve_remote_dir(BASE, bad)


# --------------------------------------------------------------------------
# The destination is appended, never substituted
# --------------------------------------------------------------------------

def test_the_email_section_resolves_to_its_own_sibling_directory():
    assert pub.expected_tail("email-marketing") == ("molosoc", "email-marketing")
    assert pub.public_url("email-marketing") == (
        "https://trafficdom.com/reports/molosoc/email-marketing/")


def test_the_analytics_section_resolves_alongside_growth_and_email():
    assert pub.expected_tail("analytics") == ("molosoc", "analytics")
    assert pub.resolve_remote_dir(BASE, "analytics") == MOLOSOC_ANALYTICS_SECTION_DIR


def test_the_zoe_social_section_resolves_under_zoes_own_directory():
    assert pub.expected_tail("social", client="zoe") == ("zoe", "social")
    assert pub.resolve_remote_dir(BASE, "social", "zoe") == ZOE_SOCIAL_DIR
    assert pub.public_url("social", "zoe") == "https://trafficdom.com/reports/zoe/social/"


def test_zoe_and_molosoc_can_never_be_the_same_directory():
    assert pub.expected_tail(client="zoe") != pub.expected_tail(client="molosoc")
    assert pub.resolve_remote_dir(BASE, client="zoe") == ZOE_DIR
    assert pub.resolve_remote_dir(BASE, client="zoe") != ANALYTICS_DIR


def test_the_two_molosoc_sections_can_never_be_the_same_directory():
    """Publishing one must not be able to replace the other."""
    assert pub.expected_tail("growth") != pub.expected_tail("email-marketing")


def test_the_remote_file_is_still_only_index_html():
    assert pub.REMOTE_FILENAME == "index.html"


# --------------------------------------------------------------------------
# The bare client directory (--directory) is a third, narrower destination
# --------------------------------------------------------------------------

def test_the_directory_flag_resolves_to_the_bare_base_path():
    assert pub.expected_tail(client=None) == ()
    assert pub.resolve_remote_dir(BASE, client=None) == BASE
    assert pub.public_url(client=None) == "https://trafficdom.com/reports/"


def test_the_directory_flag_refuses_a_section():
    with pytest.raises(pub.PublishError):
        pub.expected_tail("growth", client=None)


def test_the_directory_cli_flag_sets_client_to_none():
    args = pub.parse_args(["--directory"])
    assert args.client is None
    assert args.section is None


def test_the_directory_flag_cannot_be_combined_with_client_or_section():
    with pytest.raises(SystemExit):
        pub.parse_args(["--directory", "--client", "zoe"])
    with pytest.raises(SystemExit):
        pub.parse_args(["--directory", "--section", "growth"])


# --------------------------------------------------------------------------
# A sectioned or cross-client run may not land somewhere else
# --------------------------------------------------------------------------

def test_the_analytics_directory_is_refused_when_a_section_was_asked_for():
    """The whole point: with --section growth, `.../molosoc` is a wrong path."""
    with pytest.raises(pub.PublishError) as excinfo:
        pub.check_remote_dir(ANALYTICS_DIR, BASE, "growth")
    assert "molosoc/growth" in str(excinfo.value)


def test_zoes_directory_is_refused_for_a_molosoc_destination():
    with pytest.raises(pub.PublishError):
        pub.check_remote_dir(ZOE_DIR, BASE, client="molosoc")


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


def test_a_client_subdirectory_is_refused_for_the_bare_directory_destination():
    """--directory must resolve to exactly the base path, not a client dir
    that happens to sit under it."""
    with pytest.raises(pub.PublishError):
        pub.check_remote_dir(ANALYTICS_DIR, BASE, client=None)


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


def test_the_location_check_passes_on_zoes_social_directory():
    sftp = FakeSFTP(cwd=ZOE_SOCIAL_DIR)
    assert pub.verify_location(sftp, ZOE_SOCIAL_DIR, "social", "zoe") == ZOE_SOCIAL_DIR


def test_zoes_directory_does_not_satisfy_a_molosoc_check():
    sftp = FakeSFTP(cwd=ZOE_DIR)
    with pytest.raises(pub.PublishError):
        pub.verify_location(sftp, ANALYTICS_DIR, client="molosoc")


def test_the_directory_check_requires_an_exact_match_on_the_base_path():
    sftp = FakeSFTP(cwd=BASE)
    assert pub.verify_location(sftp, BASE, client=None) == BASE


def test_the_directory_check_rejects_a_client_subdirectory():
    """No suffix match is accepted for --directory — an exact match is the
    only thing that ever counts, since there is no tail to compare."""
    sftp = FakeSFTP(cwd=ANALYTICS_DIR)
    with pytest.raises(pub.PublishError):
        pub.verify_location(sftp, BASE, client=None)


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


def test_zoes_directory_must_already_exist_too_before_its_section_is_created():
    sftp = FakeSFTP(cwd="/", dirs=set())
    with pytest.raises(pub.PublishError):
        pub.enter_remote_dir(sftp, ZOE_SOCIAL_DIR, section="social", client="zoe")
    assert sftp.made == []

    sftp = FakeSFTP(cwd="/", dirs={ZOE_DIR})
    entered = pub.enter_remote_dir(sftp, ZOE_SOCIAL_DIR, section="social", client="zoe")
    assert entered == ZOE_SOCIAL_DIR
    assert sftp.made == [ZOE_SOCIAL_DIR]


def test_the_bare_reports_directory_is_entered_but_never_created():
    """--directory writes directly into an already-existing base path —
    nothing is ever created for this destination."""
    sftp = FakeSFTP(cwd="/", dirs={BASE})
    entered = pub.enter_remote_dir(sftp, BASE, client=None)
    assert entered == BASE
    assert sftp.made == []


def test_a_missing_base_path_is_an_error_for_the_directory_destination_too():
    sftp = FakeSFTP(cwd="/", dirs=set())
    with pytest.raises(pub.PublishError):
        pub.enter_remote_dir(sftp, BASE, client=None)
    assert sftp.made == []


# --------------------------------------------------------------------------
# Regression: the home-relative fallback must not break the bare directory
# --------------------------------------------------------------------------
#
# `home_relative` rebases a path under the account's home directory — the
# same folder FTP shows as `/public_html/...` and SSH sees as
# `<home>/public_html/...`. For a client/section destination, the rebased
# candidate is checked by descent from `home` (it just has to still end in
# the right tail and not escape). --directory has no tail at all, so that
# same check demands an EXACT match — and demanding the rebased path equal
# bare `home` can never hold, since the rebased path is always `home` plus
# something. That mismatch used to raise before the primary literal path was
# even tried, breaking --directory whenever a `home` was supplied at all —
# regardless of whether the literal chdir below would have succeeded.

def test_the_bare_reports_directory_works_even_when_a_home_is_supplied():
    """A `home` must never break the primary literal path for --directory."""
    sftp = FakeSFTP(cwd="/", dirs={BASE})
    entered = pub.enter_remote_dir(sftp, BASE, home="/home/certainuser", client=None)
    assert entered == BASE
    assert sftp.made == []


def test_the_bare_reports_directory_is_found_via_the_home_relative_fallback():
    """When only the home-relative path is reachable, it is still found —
    the fallback that already worked for client/section destinations must
    work here too, not raise before it is even tried."""
    home = "/home/certainuser"
    rebased = home + BASE
    sftp = FakeSFTP(cwd="/", dirs={rebased})
    entered = pub.enter_remote_dir(sftp, BASE, home=home, client=None)
    assert entered == rebased
    assert sftp.made == []


def test_home_relative_resolves_the_bare_reports_directory_without_raising():
    home = "/home/certainuser"
    assert pub.home_relative(BASE, home, client=None) == home + BASE


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
