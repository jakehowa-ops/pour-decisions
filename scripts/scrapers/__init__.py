"""Supermarket wine scrapers for Pour Decisions."""

from .base import BaseScraper, ScrapeResult
from .supermarkets import SCRAPERS

__all__ = ["BaseScraper", "ScrapeResult", "SCRAPERS"]
