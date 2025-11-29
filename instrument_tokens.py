"""
instrument_tokens.py

Utility to fetch the list of instruments (including their tokens) from the Kite Connect API.
It uses the shared ``get_kite`` function from ``kite_auth.py`` which handles login and token caching.
The fetched data can be saved to ``instrument_tokens.json`` for later reuse.
"""

import json
import logging
from typing import List, Dict

from kite_auth import get_kite

# ----------------------------------------------------------------------
# Configuration – you may adjust the filters as needed.
# ----------------------------------------------------------------------
# Example: limit to a specific exchange (e.g., "NSE") or instrument type ("EQ").
EXCHANGE = None  # Set to "NSE", "BSE", etc., or leave ``None`` for all.
INSTRUMENT_TYPE = None  # Set to "EQ", "FUT", "OPT", etc., or ``None``.

TOKEN_FILE = "instrument_tokens.json"


def fetch_instruments() -> List[Dict]:
    """Fetch the full instrument list from Kite Connect.

    Returns
    -------
    List[Dict]
        Each dictionary contains keys such as ``instrument_token``, ``tradingsymbol``,
        ``exchange``, and ``instrument_type``.
    """
    kite = get_kite()
    try:
        logging.info("Fetching instrument list from Kite Connect")
        instruments = kite.instruments()
        # Apply optional filters
        if EXCHANGE:
            instruments = [i for i in instruments if i.get("exchange") == EXCHANGE]
        if INSTRUMENT_TYPE:
            instruments = [i for i in instruments if i.get("instrument_type") == INSTRUMENT_TYPE]
        logging.info("Fetched %d instruments", len(instruments))
        return instruments
    except Exception as e:
        logging.error("Failed to fetch instruments: %s", e)
        raise


def save_instruments(instruments: List[Dict], filepath: str = TOKEN_FILE) -> None:
    """Persist the instrument list to a JSON file.
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(instruments, f, indent=2, ensure_ascii=False)
        logging.info("Instrument list saved to %s", filepath)
    except OSError as exc:
        logging.error("Unable to write instrument file: %s", exc)
        raise


if __name__ == "__main__":
    data = fetch_instruments()
    save_instruments(data)
