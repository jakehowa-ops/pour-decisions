"""Shared HTTP plumbing for the supermarket scrapers."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

try:  # requests is optional at runtime; the seed fallback works without it.
    import requests
except Exception:  # pragma: no cover - exercised only when requests is absent
    requests = None  # type: ignore

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


@dataclass
class ScrapeResult:
    """What a single supermarket scraper hands back to the orchestrator."""

    supermarket: str
    wines: list[dict] = field(default_factory=list)
    ok: bool = True
    error: str | None = None


class BaseScraper:
    """Base class: subclasses implement :meth:`scrape`.

    The :meth:`get` helper centralises retries, polite delays and the
    bot-friendly headers every concrete scraper needs.
    """

    supermarket: str = "Unknown"
    #: Listing pages to crawl, keyed by wine type.
    listing_urls: dict[str, str] = {}

    def __init__(self, *, delay: float = 1.5, timeout: float = 20.0, retries: int = 3):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self._session = requests.Session() if requests else None

    def get(self, url: str) -> str | None:
        """Fetch a URL with retries; returns HTML text or ``None`` on failure."""
        if self._session is None:
            return None
        backoff = 2.0
        for attempt in range(self.retries):
            try:
                resp = self._session.get(
                    url,
                    headers={"User-Agent": USER_AGENT, "Accept-Language": "en-GB,en;q=0.9"},
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    time.sleep(self.delay)  # be polite between requests
                    return resp.text
            except Exception:
                pass
            time.sleep(backoff)
            backoff *= 2
        return None

    def scrape(self) -> ScrapeResult:  # pragma: no cover - overridden by subclasses
        raise NotImplementedError
