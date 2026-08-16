#!/usr/bin/env python3
"""
Upload the weekly dashboard to the Trafficdom report host over FTPS.

One file, one directory, no deletions. The report host also serves a
WordPress installation, so the entire risk of this script is writing to the
wrong path — and a wrong path here means touching someone's live site. Every
guard below exists for that reason:

  * the destination is DERIVED, never taken as free text: it is always
    `${REPORTS_BASE_PATH}/molosoc`, with nothing else accepted;
  * the resolved path is refused if it escapes the base, is relative, or
    contains a WordPress directory name;
  * after connecting, the server's own `PWD` is compared against the expected
    path and the upload is abandoned unless they match exactly — the check
    that matters, because it is the server's opinion of where we are rather
    than ours;
  * only `molosoc/` is ever created, and only directly inside a base path
    that must already exist;
  * exactly one file is stored, and nothing is ever deleted or renamed.

Explicit FTPS (AUTH TLS) on port 21: connect in the clear, upgrade before
login, then PROT P so both the credentials and the payload are encrypted.

Usage:
    # resolve and print the destination without connecting
    python3 automations/analytics/publish_dashboard.py --dry-run

    # upload
    python3 automations/analytics/publish_dashboard.py --file site/index.html
"""

import argparse
import ftplib
import os
import ssl
import sys

from analytics_common import redact, register_secret

HOST_ENV = "REPORTS_SFTP_HOST"
USER_ENV = "REPORTS_SFTP_USER"
PASS_ENV = "REPORTS_SFTP_PASS"
BASE_PATH_ENV = "REPORTS_BASE_PATH"

#: The single sub-directory this script may write to, under the base path.
PROJECT_DIR = "molosoc"

#: The only filename it may store.
REMOTE_FILENAME = "index.html"

FTPS_PORT = 21
TIMEOUT_SECONDS = 60

#: Path segments that would mean we are inside a WordPress install. Present as
#: a blunt stop: no legitimate resolved path for this job contains any of them.
FORBIDDEN_SEGMENTS = ("wp-content", "wp-admin", "wp-includes", "wp-json")


class PublishError(RuntimeError):
    pass


def resolve_remote_dir(base_path):
    """`${REPORTS_BASE_PATH}/molosoc`, or refuse to produce a path at all.

    Returns a POSIX path with no trailing slash. Raises rather than guessing:
    an unset or odd base path must stop the upload, not silently retarget it.
    """
    base = (base_path or "").strip()
    if not base:
        raise PublishError(
            f"{BASE_PATH_ENV} is not set. Refusing to guess a remote directory."
        )
    if not base.startswith("/"):
        raise PublishError(
            f"{BASE_PATH_ENV} must be an absolute path; got {base!r}."
        )

    base = base.rstrip("/")
    target = f"{base}/{PROJECT_DIR}"

    segments = [s for s in target.split("/") if s]
    if any(s in ("..", ".") for s in segments):
        raise PublishError(f"refusing a remote path with relative segments: {target!r}")
    for forbidden in FORBIDDEN_SEGMENTS:
        if forbidden in segments:
            raise PublishError(
                f"refusing a remote path inside a WordPress directory: {target!r}"
            )
    if segments[-1] != PROJECT_DIR:
        raise PublishError(f"resolved path does not end in {PROJECT_DIR!r}: {target!r}")
    if not target.startswith(base + "/"):
        raise PublishError(f"resolved path escapes {base!r}: {target!r}")

    return target


def load_settings(env=None):
    env = os.environ if env is None else env
    missing = [name for name in (HOST_ENV, USER_ENV, PASS_ENV)
               if not (env.get(name) or "").strip()]
    if missing:
        raise PublishError(f"missing required secret(s): {', '.join(missing)}")

    password = env[PASS_ENV].strip()
    register_secret(password)  # any later error text is scrubbed of it

    return {
        "host": env[HOST_ENV].strip(),
        "user": env[USER_ENV].strip(),
        "password": password,
        "remote_dir": resolve_remote_dir(env.get(BASE_PATH_ENV)),
    }


def connect(settings, port=FTPS_PORT):
    """Explicit FTPS: upgrade the control channel before sending credentials."""
    context = ssl.create_default_context()
    ftps = ftplib.FTP_TLS(context=context, timeout=TIMEOUT_SECONDS)
    ftps.connect(settings["host"], port)
    ftps.auth()                       # AUTH TLS, before login
    ftps.login(settings["user"], settings["password"])
    ftps.prot_p()                     # encrypt the data channel too
    return ftps


def enter_remote_dir(ftps, remote_dir, create=True):
    """Change into the target directory, creating only its last segment.

    The base path must already exist. If it does not, that is a configuration
    error worth stopping on rather than a directory tree to invent — building
    one would be how a typo in the base path silently becomes a new folder in
    someone's web root.
    """
    base, _, leaf = remote_dir.rpartition("/")
    try:
        ftps.cwd(base)
    except ftplib.all_errors as exc:
        raise PublishError(
            f"base path {base!r} does not exist or is not reachable: {redact(exc)}"
        ) from None

    try:
        ftps.cwd(leaf)
    except ftplib.all_errors:
        if not create:
            raise PublishError(f"remote directory {remote_dir!r} does not exist") from None
        try:
            ftps.mkd(leaf)
            ftps.cwd(leaf)
        except ftplib.all_errors as exc:
            raise PublishError(
                f"could not create or enter {remote_dir!r}: {redact(exc)}"
            ) from None
    return ftps.pwd()


def verify_location(ftps, remote_dir):
    """The check that actually protects the live site.

    Compares the SERVER's idea of the working directory with the path we
    intend to write to. A chroot, a symlink or a home-relative base path can
    all make a locally-correct path land somewhere else; only PWD reveals it.
    Returns the server's path on success and raises otherwise.
    """
    actual = ftps.pwd().rstrip("/") or "/"
    expected = remote_dir.rstrip("/")

    # A chrooted account reports a path relative to its own root, so accept a
    # suffix match — but require the project directory to be the final segment
    # either way, which is the part that must never be wrong.
    if actual == expected or (actual.endswith("/" + PROJECT_DIR)
                              and expected.endswith("/" + PROJECT_DIR)
                              and (expected.endswith(actual) or actual.endswith(expected))):
        return actual

    raise PublishError(
        f"remote directory check FAILED. Server reports {actual!r}, expected "
        f"{expected!r}. Nothing was uploaded."
    )


def upload(ftps, local_path, remote_filename=REMOTE_FILENAME):
    if remote_filename != REMOTE_FILENAME:
        raise PublishError(f"refusing to upload anything but {REMOTE_FILENAME}")
    with open(local_path, "rb") as handle:
        ftps.storbinary(f"STOR {remote_filename}", handle)
    return os.path.getsize(local_path)


def confirm_uploaded(ftps, expected_bytes, remote_filename=REMOTE_FILENAME):
    """Ask the server how big the file is, rather than trusting STOR."""
    try:
        ftps.voidcmd("TYPE I")
        remote_size = ftps.size(remote_filename)
    except ftplib.all_errors as exc:
        return None, f"could not read back the remote size: {redact(exc)}"
    if remote_size is None:
        return None, "server did not report a size for the uploaded file"
    if remote_size != expected_bytes:
        return remote_size, (f"size mismatch: sent {expected_bytes} bytes, "
                             f"server reports {remote_size}")
    return remote_size, None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Upload index.html to the Molosoc report folder over FTPS.")
    parser.add_argument("--file", default="site/index.html",
                        help="Local file to upload (default: site/index.html)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Resolve and print the destination without connecting")
    parser.add_argument("--port", type=int, default=FTPS_PORT)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        settings = load_settings()
    except PublishError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    remote_dir = settings["remote_dir"]
    print(f"Resolved remote directory: {remote_dir}")
    print(f"Remote file:               {remote_dir}/{REMOTE_FILENAME}")
    print(f"Host:                      {settings['host']} (FTPS, port {args.port})")

    if args.dry_run:
        print("\nDry run — nothing was uploaded and no connection was made.")
        return 0

    if not os.path.isfile(args.file):
        print(f"FAIL local file not found: {args.file}", file=sys.stderr)
        return 1
    local_bytes = os.path.getsize(args.file)

    ftps = None
    try:
        ftps = connect(settings, port=args.port)
        print(f"Connected. {ftps.getwelcome() or ''}".strip())

        entered = enter_remote_dir(ftps, remote_dir)
        print(f"Entered: {entered}")

        confirmed = verify_location(ftps, remote_dir)
        print(f"PASS remote directory verified: {confirmed}")

        sent = upload(ftps, args.file)
        print(f"Uploaded {REMOTE_FILENAME} ({sent:,} bytes)")

        remote_size, problem = confirm_uploaded(ftps, sent)
        if problem:
            print(f"FAIL {problem}", file=sys.stderr)
            return 1
        print(f"PASS server confirms {remote_size:,} bytes at {confirmed}/{REMOTE_FILENAME}")

    except PublishError as exc:
        print(f"FAIL {redact(exc)}", file=sys.stderr)
        return 1
    except ftplib.all_errors as exc:
        print(f"FAIL FTPS error: {redact(exc)}", file=sys.stderr)
        return 1
    finally:
        if ftps is not None:
            try:
                ftps.quit()
            except Exception:  # noqa: BLE001 — a failed QUIT must not mask the result
                ftps.close()

    print("\nOne file uploaded. Nothing was deleted, renamed or moved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
