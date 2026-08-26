#!/usr/bin/env python3
"""
Upload the weekly dashboard to the Trafficdom report host over SFTP.

One file, one directory, no deletions. The report host also serves a
WordPress installation, so the entire risk of this script is writing to the
wrong path — and a wrong path here means touching someone's live site. Every
guard below exists for that reason:

  * the destination is DERIVED, never taken as free text: it is always
    `${REPORTS_BASE_PATH}/<client>[/<section>]` for a fixed client and a
    fixed section, both chosen from closed sets (`ALLOWED_CLIENTS`,
    `ALLOWED_SECTIONS`) — or, with `--directory`, exactly
    `${REPORTS_BASE_PATH}` itself and nothing deeper;
  * the resolved path is refused if it escapes the base, is relative, or
    contains a WordPress directory name;
  * after connecting, the server's own working directory is compared against
    the expected path and the upload is abandoned unless they match — the
    check that matters, because it is the server's opinion of where we are
    rather than ours;
  * only one segment is ever created — a client directory, or a section
    inside one that already exists — and only directly inside a base path
    that must already exist; `--directory` creates nothing at all, since
    the base path is the whole destination;
  * exactly one file is stored, and nothing is ever deleted or renamed.

Default behaviour is unchanged from before this script published more than
one client's reports: every caller that never passes `--client` still
publishes to `molosoc`, exactly as before.

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

#: The sub-directory this script writes to by default, under the base path —
#: unchanged from before this file supported more than one. Every existing
#: caller (weekly-marketing-report.yml, publish-growth-report.yml,
#: publish-email-report.yml) never passes `--client`, so this default is
#: what keeps every one of them behaving exactly as before.
PROJECT_DIR = "molosoc"

#: Every client directory this script may write to, as a FIXED SET — the
#: same discipline `ALLOWED_SECTIONS` below already applies one level
#: shallower. `--client` is an argparse choice, so an unknown value is
#: rejected by the parser before any path exists.
ALLOWED_CLIENTS = ("molosoc", "zoe")

#: Sub-sections each client directory may be written to, one level deeper —
#: a FIXED SET PER CLIENT, never free text. Adding one is a visible edit
#: here, and each entry is a directory somebody has to create.
#:
#: MOLOSOC: Analytics itself sits at the client root (no section) and is
#: never written by a sectioned run — with `--section` set, the path check
#: REFUSES a destination ending in `molosoc` alone. `growth`, `email-
#: marketing` and `analytics` are its three siblings, all published by this
#: same script, over the same connection, with the same guards —
#: deliberately, rather than by a second publisher that would have to
#: re-earn all of them. (`analytics` exists so the Analytics report can
#: also be published to its own segment, `molosoc/analytics/`, once the
#: client root moves to the Brand Overview — ADR 0043 in the Growth Engine
#: repository.)
#:
#: ZOE: only `social` exists, because only the Social report is live for
#: this client — see that repository's own `clients/zoe/channels.toml`.
ALLOWED_SECTIONS = {
    "molosoc": ("growth", "email-marketing", "analytics"),
    "zoe": ("social",),
}

#: Every section across every client, for the CLI's own early rejection of
#: an obviously-unknown value — the per-client check in `expected_tail`
#: still applies afterwards, and is the one that actually decides whether a
#: given section is valid for the given client.
ALL_SECTIONS = tuple(sorted({s for secs in ALLOWED_SECTIONS.values() for s in secs}))

#: Where a client's directory is served from. Used only to verify the
#: deployment. Derived, like every other destination here.
def public_url(section=None, client=PROJECT_DIR):
    """The address the destination is served from. Derived, like the path."""
    if client is None:
        expected_tail(section, client)  # refuses section/client set with --directory
        return "https://trafficdom.com/reports/"
    expected_tail(section, client)  # refuses an unknown client/section before building a URL
    base = f"https://trafficdom.com/reports/{client}/"
    return f"{base}{section}/" if section else base

#: The only filename it may store.
REMOTE_FILENAME = "index.html"

SSH_PORT = 22
TIMEOUT_SECONDS = 60

#: Path segments that would mean we are inside a WordPress install. Present as
#: a blunt stop: no legitimate resolved path for this job contains any of them.
FORBIDDEN_SEGMENTS = ("wp-content", "wp-admin", "wp-includes", "wp-json")


class PublishError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Destination — derived, never free text
# --------------------------------------------------------------------------

def expected_tail(section=None, client=PROJECT_DIR):
    """The segments a resolved path must end with. One place, three callers.

    ``client=None`` is the one exception to "every destination is a client
    directory": it means the bare reports directory itself — the TrafficDom
    client directory page — and refuses outright if combined with a
    section, since there is no sub-directory of the base path this script
    may create beyond one client's own.
    """
    if client is None:
        if section is not None:
            raise PublishError(
                "a section cannot be combined with client=None (the bare "
                "reports directory) — there is no sectioned path beneath it."
            )
        return ()
    if client not in ALLOWED_CLIENTS:
        raise PublishError(
            f"unknown client {client!r}; expected one of "
            f"{', '.join(ALLOWED_CLIENTS)}. Clients are a fixed set, not a "
            "path fragment."
        )
    if section is None:
        return (client,)
    if section not in ALLOWED_SECTIONS.get(client, ()):
        raise PublishError(
            f"unknown section {section!r} for client {client!r}; expected "
            f"one of {', '.join(ALLOWED_SECTIONS.get(client, ())) or '(none)'}"
            ". Sections are a fixed set, not a path fragment."
        )
    return (client, section)


def check_remote_dir(target, base, section=None, client=PROJECT_DIR):
    """Every rule a path must satisfy before it may be written to.

    Kept separate from how the path was produced, so that a path derived a
    second way — see `home_relative` — has to clear exactly the same bar
    rather than a weaker one.

    `section` deepens the destination by exactly one fixed segment. The tail
    check is what makes that safe: with a section, a path ending in the bare
    client directory is refused just as firmly as one ending anywhere else,
    so a run asked for `growth` can never land on the Analytics report one
    level up. With `client=None` (the bare reports directory), the tail is
    empty and `target` must equal `base` exactly — checked the same way,
    through the same function, rather than a separate rule.
    """
    segments = [s for s in target.split("/") if s]
    tail = expected_tail(section, client)
    if any(s in ("..", ".") for s in segments):
        raise PublishError(f"refusing a remote path with relative segments: {target!r}")
    for forbidden in FORBIDDEN_SEGMENTS:
        if forbidden in segments:
            raise PublishError(
                f"refusing a remote path inside a WordPress directory: {target!r}")
    if tail:
        if tuple(segments[-len(tail):]) != tail:
            raise PublishError(
                f"resolved path does not end in {'/'.join(tail)!r}: {target!r}")
        if not target.startswith(base + "/"):
            raise PublishError(f"resolved path escapes {base!r}: {target!r}")
    elif target != base:
        raise PublishError(
            f"client=None (the bare reports directory) must resolve to "
            f"exactly the base path {base!r}, got {target!r}"
        )

    return target


def resolve_remote_dir(base_path, section=None, client=PROJECT_DIR):
    """`${REPORTS_BASE_PATH}/<client>[/<section>]`, or refuse to produce a
    path.

    The client and section are appended, never substituted: no argument can
    replace a fixed segment with something else — `expected_tail` is the
    only place that ever decides what the tail is.
    """
    base = (base_path or "").strip() or DEFAULT_BASE_PATH
    if not base.startswith("/"):
        raise PublishError(f"{BASE_PATH_ENV} must be an absolute path; got {base!r}.")

    base = base.rstrip("/")
    tail = expected_tail(section, client)
    target = "/".join((base,) + tail) if tail else base
    return check_remote_dir(target, base, section, client)


def home_relative(remote_dir, home, section=None, client=PROJECT_DIR):
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

    rebased = home + remote_dir
    tail = expected_tail(section, client)
    # With a tail, `check_remote_dir` only needs `base` to prove the result
    # still descends from `home` (the escape check) — `home` itself is right
    # for that. With no tail (client=None), the same function instead
    # requires `target == base` exactly; passing bare `home` there would
    # compare the rebased path against a shorter one it can never equal,
    # rejecting every legitimate rebase. The rebased path IS its own
    # expected value in that case — there is no separate "tail" to prove
    # descent from — so it is its own base for that comparison.
    base_for_check = home if tail else rebased
    return check_remote_dir(rebased, base_for_check, section, client)


def load_settings(env=None, section=None, client=PROJECT_DIR):
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
        "remote_dir": resolve_remote_dir(env.get(BASE_PATH_ENV), section, client),
        "section": section,
        "client": client,
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

def enter_remote_dir(sftp, remote_dir, create=True, home=None, section=None,
                     client=PROJECT_DIR):
    """Change into the target directory, creating only its last segment.

    The base path must already exist. Building a missing tree is how a typo in
    the base path silently becomes a new folder in someone's web root — so a
    base that cannot be entered is an error, never something to create.

    With a section, "the base" is `.../molosoc`, which therefore has to exist
    already, and the one segment that may be created is `growth`. The rule is
    unchanged; it simply applies one level deeper.

    With `client=None` (the bare reports directory), there is no segment
    left for this script to create at all: `remote_dir` IS the base path,
    it must already exist, and this function only ever enters it —
    `create` has no effect in this mode, the same "never build a missing
    base" rule every other destination already follows.

    `home` allows the one alternative reading of the base path: the same
    folder addressed from inside the account's home directory, which is how
    SSH sees what FTP calls `/public_html/...`. It is tried only after the
    literal path fails, and it is checked by the same rules.
    """
    if client is None:
        candidates = [remote_dir]
        rebased = home_relative(remote_dir, home, section, client)
        if rebased is not None:
            candidates.append(rebased)
        for index, candidate in enumerate(candidates):
            try:
                sftp.chdir(candidate)
                return sftp.getcwd()
            except IOError as exc:
                if index == len(candidates) - 1:
                    raise PublishError(
                        f"reports directory {remote_dir!r} does not exist or "
                        f"is not reachable: {redact(exc)}"
                        + (f" (also tried {candidate!r})"
                           if candidate != remote_dir else "")
                    ) from None

    base, _, leaf = remote_dir.rpartition("/")

    candidates = [base]
    rebased = home_relative(remote_dir, home, section, client)
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


def verify_location(sftp, remote_dir, section=None, client=PROJECT_DIR, home=None):
    """Compare the SERVER's working directory with the one we mean to write to.

    A chroot, a symlink or a home-relative base path can each make a
    locally-correct path land somewhere else; only asking the server reveals
    it. Returns the server's path on success and raises otherwise.

    The tail is the whole point when a section is in play: publishing the
    Growth report must fail rather than succeed if the server has put us in
    `molosoc` instead of `molosoc/growth`, because that directory holds the
    live Analytics report. With `client=None` there is no tail at all, so
    only two things are ever accepted: the resolved base path itself, and —
    when `home` is available — the identical directory addressed from inside
    the account's home (the same alternate reading `enter_remote_dir` and
    `home_relative` already accept; not accepting it here too would make this
    check reject the very entry it just approved). No other suffix makes a
    wrong directory look right.
    """
    actual = (sftp.getcwd() or "").rstrip("/") or "/"
    expected = remote_dir.rstrip("/")
    tail_segments = expected_tail(section, client)

    if not tail_segments:
        acceptable = {expected}
        rebased = home_relative(remote_dir, home, section, client)
        if rebased is not None:
            acceptable.add(rebased.rstrip("/"))
        if actual in acceptable:
            return actual
        raise PublishError(
            f"remote directory check FAILED. Server reports {actual!r}, "
            f"expected exactly {expected!r}. Nothing was uploaded."
        )

    tail = "/" + "/".join(tail_segments)

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
        description="Upload index.html to a TrafficDom report destination over SFTP.")
    parser.add_argument("--file", default="site/index.html",
                        help="Local file to upload (default: site/index.html)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Resolve and print the destination without connecting")
    parser.add_argument("--port", type=int, default=SSH_PORT)
    parser.add_argument("--client", choices=ALLOWED_CLIENTS, default=None,
                        help="Which client's report directory to publish "
                             "into (default: molosoc — every existing "
                             "caller that never passes this flag keeps "
                             "publishing there). Mutually exclusive with "
                             "--directory.")
    parser.add_argument("--section", choices=ALL_SECTIONS, default=None,
                        help="Publish one level deeper, into this fixed "
                             "sub-directory of the client's report folder "
                             "(e.g. 'growth'). Must be one of the sections "
                             "that client actually has — checked again, more "
                             "specifically, before any connection is made. "
                             "Omit for that client's own report at its root.")
    parser.add_argument("--directory", action="store_true",
                        help="Publish the bare TrafficDom client directory "
                             "page itself (reports/index.html), instead of "
                             "any one client's report. Mutually exclusive "
                             "with --client/--section.")
    args = parser.parse_args(argv)
    if args.directory:
        if args.client is not None:
            parser.error("--directory cannot be combined with --client")
        if args.section is not None:
            parser.error("--directory cannot be combined with --section")
        args.client = None
    elif args.client is None:
        args.client = PROJECT_DIR
    return args


def main(argv=None):
    args = parse_args(argv)

    try:
        settings = load_settings(section=args.section, client=args.client)
    except PublishError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    remote_dir = settings["remote_dir"]
    print(f"Host:                      {settings['host']}:{args.port} "
          f"(SFTP over SSH) [{settings['host_source']}]")
    print(f"User from:                 {settings['user_source']}")
    print(f"Resolved remote directory: {remote_dir}")
    print(f"Remote file:               {remote_dir}/{REMOTE_FILENAME}")
    print(f"Client:                    {args.client or '(none — the client directory)'}")
    print(f"Section:                   {args.section or '(none — the client root)'}")
    print(f"Public URL:                {public_url(args.section, args.client)}")

    if args.dry_run:
        print("\nDry run — nothing was uploaded and no connection was made.")
        return 0

    if not os.path.isfile(args.file):
        print(f"FAIL local file not found: {args.file}", file=sys.stderr)
        return 1
    local_bytes = os.path.getsize(args.file)

    ssh_client = None
    try:
        ssh_client = connect(settings, port=args.port)
        sftp = ssh_client.open_sftp()

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
                                   section=args.section, client=args.client)
        print(f"Entered: {entered}")

        confirmed = verify_location(sftp, remote_dir, args.section, args.client, home=home)
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
        if ssh_client is not None:
            ssh_client.close()

    print(f"\nOne file uploaded ({local_bytes:,} bytes). Nothing was deleted, "
          "renamed or moved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
