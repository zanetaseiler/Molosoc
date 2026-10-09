"""Thin bridge to the existing read-only WooCommerce collector (Issue #120).

order_window.py lives in automations/woocommerce and is reused unchanged; this
only puts it on the import path and builds a client from the same read-only
REST key the Order Window workflow already uses.
"""

import os
import sys
from pathlib import Path

_WOO_DIR = str(Path(__file__).resolve().parent.parent / "woocommerce")


def load():
    if _WOO_DIR not in sys.path:
        sys.path.append(_WOO_DIR)
    import order_window
    return order_window.fetch_orders, order_window.sanitize_order


def make_client():
    key = os.environ.get("WOO_RO_CONSUMER_KEY", "")
    secret = os.environ.get("WOO_RO_CONSUMER_SECRET", "")
    if not key or not secret:
        raise RuntimeError("WOO_RO_CONSUMER_KEY / WOO_RO_CONSUMER_SECRET not set")
    load()
    import order_window
    return order_window.Client(os.environ.get("WOO_SITE_URL") or order_window.DEFAULT_SITE,
                               key, secret)
