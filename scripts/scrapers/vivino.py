"""Resolve a wine's average Vivino rating.

Vivino exposes an internal search API used by its own web client:

    GET https://www.vivino.com/api/explore/explore?q=<wine name>

It returns JSON with ``explore_vintage`` matches, each carrying a
``statistics.ratings_average`` and ``ratings_count``. We take the best
name match and read those two numbers.

In sandboxed/CI environments without egress (or when Vivino rate-limits the
request) this returns ``None`` and the orchestrator keeps the rating that
came from the seed dataset, so the pipeline degrades gracefully.
"""

from __future__ import annotations

import time
import urllib.parse

try:
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore

_API = "https://www.vivino.com/api/explore/explore"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def lookup_rating(name: str, *, timeout: float = 15.0) -> tuple[float, int] | None:
    """Return ``(average_rating, ratings_count)`` for *name*, or ``None``."""
    if requests is None:
        return None
    params = {"q": name, "min_rating": 1, "price_range_min": 0, "price_range_max": 500}
    url = f"{_API}?{urllib.parse.urlencode(params)}"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
        matches = data.get("explore_vintage", {}).get("matches", [])
        if not matches:
            return None
        stats = matches[0].get("vintage", {}).get("statistics", {})
        avg = stats.get("ratings_average")
        count = stats.get("ratings_count")
        time.sleep(1.0)  # be polite
        if avg is None:
            return None
        return round(float(avg), 1), int(count or 0)
    except Exception:
        return None
