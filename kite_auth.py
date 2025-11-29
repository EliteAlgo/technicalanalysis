"""
kite_auth.py

Utility to obtain a authenticated ``KiteConnect`` instance.
It attempts to reuse a previously saved access token (saved in ``access_token.txt``).
If the token file is missing or invalid, it performs the full login flow (including 2FA)
and writes the new token to the file for future reuse.
"""

import json
import logging
import os
from urllib.parse import urlparse, parse_qs

import pyotp
import requests
from kiteconnect import KiteConnect

# ----------------------------------------------------------------------
# Configuration – replace with your actual credentials
# ----------------------------------------------------------------------
API_KEY = "szty4dl8o9usrzxd"
API_SECRET = "50lqmgm87167jkd007mrm6zjw9auniyq"
USER_ID = "PR2888"
PASSWORD = "A@a12345"
TOTP_KEY = "7MWR7W4XZ2KZ2YBXAPAUBDBEV5LBWR32"

TOKEN_FILE = "access_token.txt"


def _save_token(token: str) -> None:
    """Persist the access token to ``TOKEN_FILE``.
    """
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(token)
        logging.info("Access token saved to %s", TOKEN_FILE)
    except OSError as exc:
        logging.error("Failed to write token file: %s", exc)
        raise


def _load_token() -> str | None:
    """Read the saved token if it exists.
    Returns ``None`` when the file is missing or empty.
    """
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            token = f.read().strip()
            return token or None
    except OSError as exc:
        logging.error("Failed to read token file: %s", exc)
        return None


def _perform_login() -> KiteConnect:
    """Execute the full Zerodha login flow and return an authenticated ``KiteConnect``.
    """
    logging.info("Starting full login flow to obtain new access token")
    session = requests.Session()

    # 1. Get login URL
    login_url = f"https://kite.trade/connect/login?v=3&api_key={API_KEY}"
    url = session.get(url=login_url).url

    # 2. Submit credentials
    resp = session.post(
        url="https://kite.zerodha.com/api/login",
        data={"user_id": USER_ID, "password": PASSWORD},
    )
    data = json.loads(resp.content)
    if data.get("status") == "error":
        raise Exception(f"Login failed: {data.get('message')}")
    request_id = data["data"]["request_id"]

    # 3. 2FA
    twofa = pyotp.TOTP(TOTP_KEY).now()
    resp = session.post(
        url="https://kite.zerodha.com/api/twofa",
        data={"user_id": USER_ID, "request_id": request_id, "twofa_value": twofa},
    )
    data = json.loads(resp.content)
    if data.get("status") == "error":
        raise Exception(f"2FA failed: {data.get('message')}")

    # 4. Get request token
    url = url + "&skip_session=true"
    redirect_url = session.get(url=url, allow_redirects=True).url
    parsed = urlparse(redirect_url)
    qs = parse_qs(parsed.query)
    if "request_token" not in qs:
        raise Exception("Request token not found in redirect URL")
    request_token = qs["request_token"][0]

    # 5. Generate session (access token)
    kite = KiteConnect(api_key=API_KEY)
    session_data = kite.generate_session(request_token, api_secret=API_SECRET)
    access_token = session_data["access_token"]
    kite.set_access_token(access_token)
    logging.info("Access token obtained successfully")
    _save_token(access_token)
    return kite


def get_kite() -> KiteConnect:
    """Return a ready‑to‑use ``KiteConnect`` instance.
    It first tries to load a saved token; if that fails it falls back to the full login.
    """
    token = _load_token()
    kite = KiteConnect(api_key=API_KEY)
    if token:
        try:
            kite.set_access_token(token)
            # A quick call to verify the token works (e.g., profile)
            kite.profile()
            logging.info("Re‑using saved access token")
            return kite
        except Exception:
            logging.warning("Saved token invalid, performing fresh login")
    # Either no token or invalid – perform full login
    return _perform_login()
