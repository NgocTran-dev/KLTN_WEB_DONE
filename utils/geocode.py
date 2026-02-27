"""Geocoding helpers (OpenStreetMap Nominatim).

This is OPTIONAL and is used only to improve map point placement.

Important: Nominatim has a usage policy (rate limits, user-agent requirements).
We keep it conservative and cache results.
"""

from __future__ import annotations

import time
from typing import Dict, Iterable, Optional, Tuple

import requests
import streamlit as st


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "KLTN-RegTech-StudentApp/1.0 (contact: demo@student)"


@st.cache_data(show_spinner=False)
def geocode_one(query: str) -> Optional[Tuple[float, float]]:
    """Geocode a single query string via Nominatim.

    Returns (lat, lon) or None.
    """
    if not query or not isinstance(query, str):
        return None

    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=20)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data:
            return None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def geocode_many(queries: Iterable[str], sleep_sec: float = 1.0) -> Dict[str, Tuple[float, float]]:
    """Geocode many unique queries with caching.

    Notes
    -----
    - This function is intentionally slow (rate-limited) to respect Nominatim.
    - Results are cached by Streamlit.
    """
    out: Dict[str, Tuple[float, float]] = {}
    seen = set()

    for q in queries:
        if q in seen:
            continue
        seen.add(q)

        coord = geocode_one(q)
        if coord is not None:
            out[q] = coord

        # Respect Nominatim usage policy
        time.sleep(max(0.0, float(sleep_sec)))

    return out
