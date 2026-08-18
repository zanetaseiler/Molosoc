#!/usr/bin/env python3
"""
Upload the weekly dashboard to the Trafficdom report host over SFTP.

One file, one directory, no deletions. The report host also serves a
WordPress installation, so the entire risk of this script is writing to the
wrong path — and a wrong path here means touching someone's live site. Every
guard below exists for that reason:

  * the destination is DERIVED, never taken as free text: it is always
    `${REPORTS_BASE_PATH}/molosoc`, with nothing else accepted;
  * the resolved path is refused if it escapes the base, is relative, or
    contains a WordPress directory name;
  * after connecting, the server's own working directory is compared against
    the expected path and the upload is abandoned unless they match — the
    check that matters, because it is the server's opinion of where we are
    rather than ours;
  * only `molosoc/` is ever created, and only directly inside a base path
    that must already exist;
  * exactly one file is stored, and nothing is ever deleted or renamed.

WHY NOT FTPS

FTPS was abandoned deliberately rather than for convenience. This is GoDaddy
shared hosting, and its FTP service presents GoDaddy's own internal
certificate for `*.prod.phx3.secureserver.net`. Verifying that honestly needs
a hostname under a domain nobody here controls, so the only way to make FTPS
work was to stop checking the certificate. SSH authenticates the server by
host key instead, which is a check we can actually perform and record.

HOST KEY

A CI runner is new every time and has no `known_hosts`, so first contact has
nothing to compare against. Two modes:

  * `REPORTS_SSH_HOST_KEY` set — the key is pinned, and a server presenting
    anything else aborts the run. This is the strong mode.
  * unset — the key is accepted and its fingerprint printed prominently, so
    it can be checked once against cPanel and then pinned. It is printed on
    every run, so a host key that changes underneath you is visible.

Usage:
    # resolve and print the destination without connecting
    python3 automations/analytics/publish_dashboard.py --dry-run

    # upload
    python3 automations/analytics/publish_dashboard.py --file site/index.html
"""

import argparse
import base64
import hashlib
import io
import os
import posixpath
import socket
import stat
import sys

from analytics_common import redact, register_secret

HOST_ENV = "REPORTS_SSH_HOST"
USER_ENV = "REPORTS_SSH_USER"
KEY_ENV = "REPORTS_SSH_KEY"
HOST_KEY_ENV = "REPORTS_SSH_HOST_KEY"
BASE_PATH_ENV = "REPORTS_BASE_PATH"

#: On GoDaddy cPanel the SSH account is normally the same as the FTP account,
#: so the existing secret is reused unless REPORTS_SSH_USER says otherwise.
#: This is what kept the move to SFTP down to a single new secret.
FALLBACK_USER_ENV = "REPORTS_SFTP_USER"

#: The server cPanel reports for this account. Committed rather than required
#: as a variable, for the same reason as the base path: an unset variable must
#: not quietly become a missing dashboard every week.
DEFAULT_SSH_HOST = "p3plmcpnl502709.prod.phx3.secureserver.net"

DEFAULT_BASE_PATH = "/public_html/Trafficdom.com/reports"

#: The single sub-directory this script may write to, under the base path.
PROJECT_DIR = "molosoc"

#: Sub-sections of that directory this script may write to, one level deeper.
#: A FIXED SET, never free text: `--section` is an argparse choice, so an
#: unknown value is rejected by the parser before any path exists. Adding one is
#: a visible edit here, and each entry is a directory somebody has to create.
#:
#: The Growth report lives in `molosoc/growth/`. It is published by this same
#: script, over the same connection, with the same guards — deliberately, rather
#: than by a second publisher that would have to re-earn all of them.
ALLOWED_SECTIONS = ("growth",)

#: Where that directory is served from. Used only to verify the deployment.
PUBLIC_URL = "https://trafficdom.com/reports/molosoc/"

#: The only filename it may store.
REMOTE_FILENAME = "index.html"

SSH_PORT = 22
TIMEOUT_SECONDS = 60

#: Path segments that would mean we are inside a WordPress install. Present as
#: a blunt stop: no legitimate resolved path for this job contains any of them.
FORBIDDEN_SEGMENTS = ("wp-content", "wp-admin", "wp-includes", "wp-json")


class PublishError(RuntimeError):
    pass


def public_url(section=None):
    """The address the destination is served from. Derived, like the path."""
    if section is None:
        return PUBLIC_URL
    expected_tail(section)  # refuses an unknown section before building a URL
    return f"{PUBLIC_URL}{section}/"


# --------------------------------------------------------------------------
# Destination — derived, never free text
# --------------------------------------------------------------------------

def expected_tail(section=None):
    """The segments a resolved path must end with. One place, three callers."""
    if section is None:
        return (PROJECT_DIR,)
    if section not in ALLOWED_SECTIONS:
        raise PublishError(
            f"unknown section {section!r}; expected one of "
            f"{', '.join(ALLOWED_SECTIONS)}. Sections are a fixed set, not a "
            "path fragment."
        )
    return (PROJECT_DIR, section)


def check_remote_dir(target, base, section=None):
    """Every rule a path must satisfy before it may be written to.

    Kept separate from how the path was produced, so that a path derived a
    second way — see `home_relative` — has to clear exactly the same bar
    rather than a weaker one.

    `section` deepens the destination by exactly one fixed segment. The tail
    check is what makes that safe: with a section, a path ending in `molosoc`
    is refused just as firmly as one ending anywhere else, so a run asked for
    `growth` can never land on the Analytics report one level up.
    """
    segments = [s for s in target.split("/") if s]
    tail = expected_tail(section)
    if any(s in ("..", ".") for s in segments):
        raise PublishError(f"refusing a remote path with relative segments: {target!r}")
    for forbidden in FORBIDDEN_SEGMENTS:
        if forbidden in segments:
            raise PublishError(
                f"refusing a remote path inside a WordPress directory: {target!r}")
    if tuple(segments[-len(tail):]) != tail:
        raise PublishError(
            f"resolved path does not end in {'/'.join(tail)!r}: {target!r}")
    if not target.startswith(base + "/"):
        raise PublishError(f"resolved path escapes {base!r}: {target!r}")

    return target


def resolve_remote_dir(base_path, section=None):
    """`${REPORTS_BASE_PATH}/molosoc[/<section>]`, or refuse to produce a path.

    The section is appended, never substituted: the Analytics report's own
    directory remains the parent of every sectioned path, and no argument can
    replace `molosoc` with something else.
    """
    base = (base_path or "").strip() or DEFAULT_BASE_PATH
    if not base.startswith("/"):
        raise PublishError(f"{BASE_PATH_ENV} must be an absolute path; got {base!r}.")

    base = base.rstrip("/")
    target = "/".join((base,) + expected_tail(section))
    return check_remote_dir(target, base, section)


def home_relative(remote_dir, home, section=None):
    """The same derived path, read from inside the account's home directory.

    FTP and SSH disagree about what `/public_html/...` means on cPanel. FTP
    drops you in the account home and treats it as the root, so the base path
    was written the way FTP displays it; SSH gives you the real filesystem,
    where that same path is an absolute one that does not exist. The
    destination is unchanged — this is the identical folder under the name the
    other protocol uses for it, not a second place to try.

    Returns None when the idea does not apply, so the caller has nothing to
    fall back to rather than something plausible-looking.
    """
    home = (home or "").rstrip("/")
    if not home.startswith("/") or home == "/":
        return None
    if remote_dir.startswith(home + "/"):
        return None  # already inside the home directory; nothing to add
    return check_remote_dir(home + remote_dir, home, section)


def load_settings(env=None, section=None):
    env = os.environ if env is None else env

    user = (env.get(USER_ENV) or env.get(FALLBACK_USER_ENV) or "").strip()
    key_material = (env.get(KEY_ENV) or "").strip()

    missing = []
    if not user:
        missing.append(f"{USER_ENV} (or {FALLBACK_USER_ENV})")
    if not key_material:
        missing.append(KEY_ENV)
    if missing:
        raise PublishError(f"missing required secret(s): {', '.join(missing)}")

    register_secret(key_material)  # any later error text is scrubbed of it

    return {
        "host": (env.get(HOST_ENV) or "").strip() or DEFAULT_SSH_HOST,
        "user": user,
        "key": key_material,
        "host_key": (env.get(HOST_KEY_ENV) or "").strip(),
        "remote_dir": resolve_remote_dir(env.get(BASE_PATH_ENV), section),
        "section": section,
        "user_source": USER_ENV if (env.get(USER_ENV) or "").strip()
                       else FALLBACK_USER_ENV,
        "host_source": HOST_ENV if (env.get(HOST_ENV) or "").strip()
                       else "committed default",
    }


# --------------------------------------------------------------------------
# SSH
# --------------------------------------------------------------------------

def load_private_key(material):
    """Parse the key, trying each type rather than trusting the header.

    Accepts raw PEM/OpenSSH text or base64 of it: a multi-line secret pasted
    into a single-line field is the classic way this goes wrong, and failing
    with "could not parse" when the fix is "decode it first" wastes a round
    trip.
    """
    import paramiko

    text = material
    if "PRIVATE KEY" not in text:
        try:
            text = base64.b64decode(text, validate=True).decode("utf-8")
        except Exception:  # noqa: BLE001 — fall through to the message below
            pass
    if "PRIVATE KEY" not in text:
        raise PublishError(
            f"{KEY_ENV} does not contain a private key. Paste the whole private "
            "key file including its BEGIN and END lines, or the base64 of it."
        )
    if not text.endswith("\n"):
        text += "\n"

    errors = []
    for key_class in (paramiko.Ed25519Key, paramiko.RSAKey,
                      paramiko.ECDSAKey, paramiko.DSSKey):
        try:
            return key_class.from_private_key(io.StringIO(text))
        except Exception as exc:  # noqa: BLE001 — try the next type
            errors.append(f"{key_class.__name__}: {exc}")

    raise PublishError(
        f"{KEY_ENV} could not be parsed as any supported key type. If the key "
        "has a passphrase it must be removed — a CI job cannot type one. "
        f"({'; '.join(errors)})"
    )


def fingerprint(host_key):
    """SHA256 fingerprint, in the form both ssh and cPanel display."""
    digest = hashlib.sha256(host_key.asbytes()).digest()
    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


def connect(settings, port=SSH_PORT, out=None):
    """Open an authenticated SSH connection. Returns the client."""
    import paramiko

    out = out or sys.stdout
    client = paramiko.SSHClient()
    expected = settings.get("host_key")

    if expected:
        client.set_missing_host_key_policy(paramiko.RejectPolicy())
        try:
            key_type, key_blob = expected.split()[:2]
            client.get_host_keys().add(
                settings["host"], key_type,
                paramiko.PKey.from_type_string(key_type, base64.b64decode(key_blob)))
        except Exception as exc:  # noqa: BLE001
            raise PublishError(
                f"{HOST_KEY_ENV} could not be parsed: {exc}. It should be the "
                "'<type> <base64>' pair from a known_hosts line."
            ) from None
    else:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=settings["host"], port=port, username=settings["user"],
            pkey=load_private_key(settings["key"]),
            timeout=TIMEOUT_SECONDS, allow_agent=False, look_for_keys=False,
        )
    except Exception:
        client.close()
        raise

    host_key = client.get_transport().get_remote_server_key()
    if expected:
        print(f"Host key pinned and matched: {fingerprint(host_key)}", file=out)
    else:
        print(f"Host key accepted on first use: {fingerprint(host_key)}", file=out)
        print(f"  Verify it once against cPanel, then pin it by setting "
              f"{HOST_KEY_ENV} to:", file=out)
        print(f"  {host_key.get_name()} "
              f"{base64.b64encode(host_key.asbytes()).decode('ascii')}", file=out)
    return client


# --------------------------------------------------------------------------
# The upload
# --------------------------------------------------------------------------

def enter_remote_dir(sftp, remote_dir, create=True, home=None, section=None):
    """Change into the target directory, creating only its last segment.

    The base path must already exist. Building a missing tree is how a typo in
    the base path silently becomes a new folder in someone's web root — so a
    base that cannot be entered is an error, never something to create.

    With a section, "the base" is `.../molosoc`, which therefore has to exist
    already, and the one segment that may be created is `growth`. The rule is
    unchanged; it simply applies one level deeper.

    `home` allows the one alternative reading of the base path: the same
    folder addressed from inside the account's home directory, which is how
    SSH sees what FTP calls `/public_html/...`. It is tried only after the
    literal path fails, and it is checked by the same rules.
    """
    base, _, leaf = remote_dir.rpartition("/")

    candidates = [base]
    rebased = home_relative(remote_dir, home, section)
    if rebased is not None:
        candidates.append(rebased.rpartition("/")[0])

    for index, candidate in enumerate(candidates):
        try:
            sftp.chdir(candidate)
            base = candidate
            break
        except IOError as exc:
            if index == len(candidates) - 1:
                raise PublishError(
                    f"base path {base!r} does not exist or is not reachable: "
                    f"{redact(exc)}"
                    + (f" (also tried {candidate!r})" if candidate != base else "")
                ) from None

    try:
        sftp.chdir(leaf)
    except IOError:
        if not create:
            raise PublishError(
                f"remote directory {remote_dir!r} does not exist") from None
        try:
            sftp.mkdir(leaf)
            sftp.chdir(leaf)
        except IOError as exc:
            raise PublishError(
                f"could not create or enter {remote_dir!r}: {redact(exc)}"
            ) from None
    return sftp.getcwd()


def verify_location(sftp, remote_dir, section=None):
    """Compare the SERVER's working directory with the one we mean to write to.

    A chroot, a symlink or a home-relative base path can each make a
    locally-correct path land somewhere else; only asking the server reveals
    it. Returns the server's path on success and raises otherwise.

    The tail is the whole point when a section is in play: publishing the
    Growth report must fail rather than succeed if the server has put us in
    `molosoc` instead of `molosoc/growth`, because that directory holds the
    live Analytics report.
    """
    actual = (sftp.getcwd() or "").rstrip("/") or "/"
    expected = remote_dir.rstrip("/")
    tail = "/" + "/".join(expected_tail(section))

    # A chrooted account reports a path relative to its own root, so accept a
    # suffix match — but require the derived tail to be the final segment(s)
    # either way, which is the part that must never be wrong.
    if actual == expected or (actual.endswith(tail)
                              and expected.endswith(tail)
                              and (expected.endswith(actual)
                                   or actual.endswith(expected))):
        return actual

    raise PublishError(
        f"remote directory check FAILED. Server reports {actual!r}, expected "
        f"{expected!r}. Nothing was uploaded."
    )


def upload(sftp, local_path, remote_filename=REMOTE_FILENAME):
    if remote_filename != REMOTE_FILENAME:
        raise PublishError(f"refusing to upload anything but {REMOTE_FILENAME}")
    sftp.put(local_path, remote_filename)
    return os.path.getsize(local_path)


def confirm_uploaded(sftp, expected_bytes, remote_filename=REMOTE_FILENAME):
    """Ask the server how big the file is, rather than trusting the transfer."""
    try:
        attrs = sftp.stat(remote_filename)
    except IOError as exc:
        return None, f"could not stat the uploaded file: {redact(exc)}"
    if stat.S_ISDIR(attrs.st_mode):
        return None, f"{remote_filename} is a directory on the server"
    if attrs.st_size != expected_bytes:
        return attrs.st_size, (f"size mismatch: sent {expected_bytes} bytes, "
                               f"server reports {attrs.st_size}")
    return attrs.st_size, None


# --------------------------------------------------------------------------
# Diagnostics
# --------------------------------------------------------------------------

def resolve(name):
    """Every address a name resolves to, or an empty list if it does not."""
    try:
        return sorted({info[4][0] for info in socket.getaddrinfo(name, None)})
    except OSError:
        return []


def describe_public_key(pkey):
    """The public half of the loaded key, as cPanel and known_hosts write it.

    Printed only when authentication fails, and safe to print: it is the
    public half. It is also the only thing that can settle the question the
    failure raises — whether the private key in the secret is the pair of the
    key authorized on the server — because everything else about the key is
    invisible from here. Comparing this fingerprint against the one cPanel
    lists beside `molosoc-reports-ci` answers it in one look.
    """
    blob = base64.b64encode(pkey.asbytes()).decode("ascii")
    digest = hashlib.sha256(pkey.asbytes()).digest()
    return (f"{pkey.get_name()} {blob}",
            "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("="))


def describe_user_shape(user):
    """Say what is notable about the username without disclosing it.

    The username is a secret, but its *shape* decides this failure: cPanel
    grants SSH to the account user only, so an FTP sub-account name — the
    `name@domain` form — authenticates over FTP and is rejected over SSH even
    when the key is perfect. That distinction is worth surfacing, and it can
    be surfaced without printing the name.
    """
    user = user or ""
    notes = []
    if "@" in user:
        notes.append("the username contains '@', which is the FTP sub-account "
                     "form. cPanel grants SSH to the main account user only, so "
                     "an FTP sub-account is refused here however good the key is "
                     f"— set {USER_ENV} to the cPanel account username.")
    if any(ch.isspace() for ch in user):
        notes.append("the username contains whitespace, which is almost "
                     "certainly a stray newline or space in the secret.")
    return notes


def describe_host_shape(host):
    """Say what is wrong with a hostname without disclosing it."""
    host = host or ""
    notes = []
    if "://" in host:
        scheme = host.split("://", 1)[0]
        notes.append(f"it starts with {scheme!r}:// — use a bare hostname, not a URL")
    if "/" in host.split("://")[-1]:
        notes.append("it contains '/' — a hostname carries no path")
    remainder = host.split("://")[-1].split("/")[0]
    if ":" in remainder:
        notes.append("it contains ':' — set the port with --port, not in the host")
    if any(ch.isspace() for ch in host):
        notes.append("it contains whitespace")
    if remainder and "." not in remainder:
        notes.append("it has no dot — that is a bare label, not a fully "
                     "qualified hostname")
    if not notes:
        notes.append("its shape looks like a hostname, so the name itself may be "
                     "wrong, or DNS for it is unavailable from the runner")
    return notes


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Upload index.html to the Molosoc report folder over SFTP.")
    parser.add_argument("--file", default="site/index.html",
                        help="Local file to upload (default: site/index.html)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Resolve and print the destination without connecting")
    parser.add_argument("--port", type=int, default=SSH_PORT)
    parser.add_argument("--section", choices=ALLOWED_SECTIONS, default=None,
                        help="Publish one level deeper, into this fixed "
                             "sub-directory of the report folder (e.g. "
                             "'growth'). Omit for the Analytics dashboard "
                             "itself. Not a path: unknown values are rejected "
                             "by the parser.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        settings = load_settings(section=args.section)
    except PublishError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    remote_dir = settings["remote_dir"]
    print(f"Host:                      {settings['host']}:{args.port} "
          f"(SFTP over SSH) [{settings['host_source']}]")
    print(f"User from:                 {settings['user_source']}")
    print(f"Resolved remote directory: {remote_dir}")
    print(f"Remote file:               {remote_dir}/{REMOTE_FILENAME}")
    print(f"Section:                   {args.section or '(none — the dashboard)'}")
    print(f"Public URL:                {public_url(args.section)}")

    if args.dry_run:
        print("\nDry run — nothing was uploaded and no connection was made.")
        return 0

    if not os.path.isfile(args.file):
        print(f"FAIL local file not found: {args.file}", file=sys.stderr)
        return 1
    local_bytes = os.path.getsize(args.file)

    client = None
    try:
        client = connect(settings, port=args.port)
        sftp = client.open_sftp()

        # Where the server puts us before we go anywhere: on cPanel this is
        # the account home, and it is what makes the FTP-style base path
        # resolvable over SSH.
        try:
            home = sftp.normalize(".")
        except Exception:  # noqa: BLE001 — only costs the fallback
            home = None
        if home:
            print(f"Session home:              {home}")

        entered = enter_remote_dir(sftp, remote_dir, home=home,
                                   section=args.section)
        print(f"Entered: {entered}")

        confirmed = verify_location(sftp, remote_dir, args.section)
        print(f"PASS remote directory verified: {confirmed}")

        sent = upload(sftp, args.file)
        print(f"Uploaded {REMOTE_FILENAME} ({sent:,} bytes)")

        remote_size, problem = confirm_uploaded(sftp, sent)
        if problem:
            print(f"FAIL {problem}", file=sys.stderr)
            return 1
        print(f"PASS server confirms {remote_size:,} bytes at "
              f"{posixpath.join(confirmed, REMOTE_FILENAME)}")

    except PublishError as exc:
        print(f"FAIL {redact(exc)}", file=sys.stderr)
        return 1
    except socket.gaierror as exc:
        print(f"FAIL could not resolve the report host: {redact(exc)}",
              file=sys.stderr)
        for note in describe_host_shape(settings["host"]):
            print(f"    - {note}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — incl. paramiko auth/SSH errors
        name = type(exc).__name__
        print(f"FAIL SSH/SFTP error ({name}): {redact(exc)}", file=sys.stderr)
        if "Authentication" in name:
            print("  The server accepted the connection and refused the "
                  "credentials, so the host, the port and the key file itself "
                  "are all fine. Exactly one of two things is wrong: the key is "
                  "not the one authorized, or the username is not the one it is "
                  f"authorized for (currently from {settings['user_source']}).",
                  file=sys.stderr)
            for note in describe_user_shape(settings["user"]):
                print(f"    - {note}", file=sys.stderr)
            try:
                line, digest = describe_public_key(load_private_key(settings["key"]))
            except PublishError:
                pass
            else:
                print(f"    - the key in {KEY_ENV} has this public half. Compare "
                      "the fingerprint with the one cPanel lists beside the "
                      "authorized key; if they differ, the wrong key is in the "
                      "secret. If cPanel lists it but shows it as not "
                      "authorized, authorize it there.", file=sys.stderr)
                print(f"      {digest}", file=sys.stderr)
                print(f"      {line}", file=sys.stderr)
        elif "BadHostKey" in name:
            print(f"  The server's host key does not match {HOST_KEY_ENV}.",
                  file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()

    print(f"\nOne file uploaded ({local_bytes:,} bytes). Nothing was deleted, "
          "renamed or moved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
