"""Per-supermarket scrapers.

Each scraper crawls the wine listing pages for the supermarket, extracts the
product name and price, and tags each bottle with a wine ``type``. Average
Vivino scores are added later by the orchestrator via :mod:`scrapers.vivino`.

The CSS selectors below reflect each retailer's product-card markup. Retailers
change their markup and bot defences often, so each scraper is defensive: if a
page can't be fetched or parsed it returns ``ok=False`` and the orchestrator
falls back to the curated seed dataset for that supermarket.
"""

from __future__ import annotations

from .base import BaseScraper, ScrapeResult

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None  # type: ignore

WINE_TYPES = ["red", "white", "rose", "sparkling"]


class _CssScraper(BaseScraper):
    """Generic scraper driven by per-retailer CSS selectors.

    Subclasses set ``listing_urls`` (type -> url) and the ``*_sel`` selectors.
    """

    card_sel: str = ""
    name_sel: str = ""
    price_sel: str = ""

    def _parse_price(self, text: str) -> float | None:
        import re

        m = re.search(r"(\d+(?:\.\d{1,2})?)", text.replace(",", ""))
        return float(m.group(1)) if m else None

    def scrape(self) -> ScrapeResult:
        if BeautifulSoup is None or not self.listing_urls:
            return ScrapeResult(self.supermarket, ok=False, error="parser/urls unavailable")

        wines: list[dict] = []
        for wtype, url in self.listing_urls.items():
            html = self.get(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            for card in soup.select(self.card_sel):
                name_el = card.select_one(self.name_sel)
                price_el = card.select_one(self.price_sel)
                if not name_el or not price_el:
                    continue
                price = self._parse_price(price_el.get_text())
                if price is None:
                    continue
                wines.append(
                    {
                        "name": name_el.get_text(strip=True),
                        "supermarket": self.supermarket,
                        "type": wtype,
                        "price": price,
                    }
                )

        ok = bool(wines)
        return ScrapeResult(
            self.supermarket,
            wines=wines,
            ok=ok,
            error=None if ok else "no products parsed",
        )


class WaitroseScraper(_CssScraper):
    supermarket = "Waitrose"
    listing_urls = {
        "red": "https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/wine/red_wine",
        "white": "https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/wine/white_wine",
        "rose": "https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/wine/rose_wine",
        "sparkling": "https://www.waitrose.com/ecom/shop/browse/groceries/beer_wine_and_spirits/champagne_and_sparkling_wine",
    }
    card_sel = "article[data-product]"
    name_sel = "[data-test='product-pod-name']"
    price_sel = "[data-test='product-pod-price']"


class MarksSpencerScraper(_CssScraper):
    supermarket = "M&S"
    listing_urls = {
        "red": "https://www.marksandspencer.com/l/food-and-wine/wine/red-wine",
        "white": "https://www.marksandspencer.com/l/food-and-wine/wine/white-wine",
        "rose": "https://www.marksandspencer.com/l/food-and-wine/wine/rose-wine",
        "sparkling": "https://www.marksandspencer.com/l/food-and-wine/champagne-and-sparkling-wine",
    }
    card_sel = "div.product-card"
    name_sel = "a.product-card__title"
    price_sel = "span.product-card__price"


class OcadoScraper(_CssScraper):
    supermarket = "Ocado"
    listing_urls = {
        "red": "https://www.ocado.com/browse/beer-wine-spirits-44588/wine-44589/red-wine-44590",
        "white": "https://www.ocado.com/browse/beer-wine-spirits-44588/wine-44589/white-wine-44597",
        "rose": "https://www.ocado.com/browse/beer-wine-spirits-44588/wine-44589/rose-wine-44603",
        "sparkling": "https://www.ocado.com/browse/beer-wine-spirits-44588/champagne-sparkling-wine-44607",
    }
    card_sel = "li.fops-item"
    name_sel = "a.fops-product__name"
    price_sel = "span.fops-price"


class AldiScraper(_CssScraper):
    supermarket = "Aldi"
    listing_urls = {
        "red": "https://groceries.aldi.co.uk/en-GB/drinks/wine/red-wine",
        "white": "https://groceries.aldi.co.uk/en-GB/drinks/wine/white-wine",
        "rose": "https://groceries.aldi.co.uk/en-GB/drinks/wine/rose-wine",
        "sparkling": "https://groceries.aldi.co.uk/en-GB/drinks/sparkling-wine-champagne",
    }
    card_sel = "div.product-tile"
    name_sel = "a.product-tile__name"
    price_sel = "span.base-price__regular"


class LidlScraper(_CssScraper):
    supermarket = "Lidl"
    listing_urls = {
        "red": "https://www.lidl.co.uk/c/red-wine/c2516",
        "white": "https://www.lidl.co.uk/c/white-wine/c2517",
        "rose": "https://www.lidl.co.uk/c/rose-wine/c2518",
        "sparkling": "https://www.lidl.co.uk/c/sparkling-wine-champagne/c2519",
    }
    card_sel = "div.ods-tile"
    name_sel = "span.ods-tile__name"
    price_sel = "span.ods-price__value"


class TescoScraper(_CssScraper):
    supermarket = "Tesco"
    listing_urls = {
        "red": "https://www.tesco.com/groceries/en-GB/shop/drinks/wine/red-wine",
        "white": "https://www.tesco.com/groceries/en-GB/shop/drinks/wine/white-wine",
        "rose": "https://www.tesco.com/groceries/en-GB/shop/drinks/wine/rose-wine",
        "sparkling": "https://www.tesco.com/groceries/en-GB/shop/drinks/champagne-and-sparkling-wine",
    }
    card_sel = "li.product-list--list-item"
    name_sel = "a[data-auto='product-tile--title']"
    price_sel = "p.beans-price__text"


class SainsburysScraper(_CssScraper):
    supermarket = "Sainsbury's"
    listing_urls = {
        "red": "https://www.sainsburys.co.uk/gol-ui/groceries/drinks/wine/red-wine/c:1043913",
        "white": "https://www.sainsburys.co.uk/gol-ui/groceries/drinks/wine/white-wine/c:1043914",
        "rose": "https://www.sainsburys.co.uk/gol-ui/groceries/drinks/wine/rose-wine/c:1043915",
        "sparkling": "https://www.sainsburys.co.uk/gol-ui/groceries/drinks/champagne-and-sparkling-wine/c:1043916",
    }
    card_sel = "div.pt-grid-item"
    name_sel = "a.pt__link"
    price_sel = "span.pt__cost__retail-price"


SCRAPERS = [
    WaitroseScraper,
    MarksSpencerScraper,
    OcadoScraper,
    AldiScraper,
    LidlScraper,
    TescoScraper,
    SainsburysScraper,
]
