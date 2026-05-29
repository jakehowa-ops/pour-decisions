"""Resolve a wine's average Vivino rating (and bottle photo) from Vivino.

Vivino's web search renders the first results server-side, so a plain HTTP GET
of::

    https://www.vivino.com/search/wines?q=<wine name>

returns HTML whose first wine card carries the community ``ratings_average``,
the wine's canonical name, a bottle-shot image URL and a link to the wine page.

Matching is the tricky part: supermarket *own-label* wines (e.g. "Tesco Finest
Barolo") usually have no Vivino page of their own, so a search would surface
*some* Barolo and hand back the wrong score. To avoid silently degrading the
curated data we only accept a live result when we're confident it's the same
wine — the producer/brand token must match and most query tokens must appear in
the result. When we're not confident (or there's no network) we return ``None``
and the caller keeps the curated seed value.
"""

from __future__ import annotations

import html as ihtml
import re
import time
import urllib.parse

try:
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore

_SEARCH = "https://www.vivino.com/search/wines"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
}

# Own-label / range words to drop before searching and before scoring the match,
# plus generic descriptors that shouldn't count towards a confident match.
_NOISE = {
    # supermarket own-label ranges
    "waitrose", "blueprint", "m&s", "found", "classics", "ocado", "aldi",
    "specially", "selected", "exquisite", "collection", "lidl", "deluxe",
    "tesco", "finest", "sainsbury's", "taste", "the", "difference",
    # generic wine words
    "wine", "red", "white", "rose", "rosé", "sparkling", "brut", "spumante",
    "superiore", "reserva", "gran", "doc", "docg", "nv", "n.v", "cru",
    "premier", "blanc", "de", "noirs", "di",
}
_STRONG_STOP = _NOISE | {
    # region / grape / style words that are common across many wines — a match
    # on these alone does NOT mean it's the same wine, so they don't count as a
    # confident "brand" signal.
    "rioja", "chablis", "barolo", "prosecco", "champagne", "malbec", "syrah",
    "shiraz", "tempranillo", "chardonnay", "sauvignon", "pinot", "grigio",
    "gris", "noir", "merlot", "grenache", "cinsault", "corvina", "nerello",
    "mascalese", "touriga", "nacional", "assyrtiko", "nebbiolo", "cortese",
    "glera", "picpoul", "cremant", "crémant", "appassimento",
    "provence", "rhone", "rhône", "valpolicella", "amarone", "gavi", "douro",
    "sancerre", "marlborough", "mendoza", "veneto", "languedoc", "loire",
    "burgundy", "piedmont", "sicily", "jura", "côtes", "cotes", "du", "villages",
    "pinet", "conegliano", "valdobbiadene", "spumante",
    # appellation names that are NOT producers, so an own-label wine named after
    # one ("M&S Châteauneuf-du-Pape") must not anchor on them.
    "châteauneuf", "chateauneuf", "pape", "marone", "centenario",
    # "veuve" collides between the real brand (Veuve Clicquot, anchored by
    # "clicquot") and Aldi's own-label "Veuve Monsigny" (anchored by nothing).
    "veuve",
    # Italian/French connector words that read as 4+ char tokens but carry no
    # brand signal ("Amarone della Valpolicella").
    "della", "delle", "dei", "del",
    # range / tier descriptors that read like names but aren't producers
    "classic", "cuvée", "cuvee", "private", "bin", "alta", "gold", "pure",
    "yellow", "label", "trilogy", "romeo", "juliet", "monsigny", "senneval",
    "comte", "conte", "priuli", "oudinot",
}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[\w'&.]+", text.lower()) if not t.isdigit()]


def _clean_query(name: str) -> str:
    """Strip own-label range words so the search hits the real producer."""
    kept = [t for t in _tokens(name) if t not in _NOISE]
    return " ".join(kept) if kept else name


def _is_confident(query: str, matched: str) -> bool:
    """True when *matched* is plausibly the same wine as *query*."""
    q = [t for t in _tokens(query) if t not in _NOISE]
    m = set(_tokens(matched))
    if not q:
        return False
    coverage = sum(t in m for t in q) / len(q)
    # A distinctive producer/brand token (4+ chars, not a region/grape/range
    # word) MUST appear in the match. This is what stops own-label wines —
    # "Waitrose Rioja Reserva", "Nyetimber Classic Cuvée" — from matching some
    # unrelated wine that merely shares a grape or range word.
    strong = [t for t in q if t not in _STRONG_STOP and len(t) >= 4]
    if not strong:
        return False  # nothing distinctive to anchor on -> never confident
    strong_ok = any(t in m for t in strong)
    return coverage >= 0.6 and strong_ok


def _parse_first_card(doc: str) -> dict | None:
    i = doc.find("wineCardContent")
    if i == -1:
        return None
    block = doc[i : i + 3500]
    name = re.search(r'aria-label="([^"]+)"', block)
    rating = re.search(r"vivinoRating__averageValue--\w+\">([0-9]\.[0-9])", block)
    img = re.search(r"images\.vivino\.com/thumbs/([A-Za-z0-9_\-]+\.png)", block)
    href = re.search(r'href="(/[a-z]{2}/[^"]+)"', block)
    if not (name and rating):
        return None
    return {
        "name": ihtml.unescape(name.group(1)),
        "vivino": float(rating.group(1)),
        "image": ("https://images.vivino.com/thumbs/" + img.group(1)) if img else None,
        "url": ("https://www.vivino.com" + ihtml.unescape(href.group(1))) if href else None,
    }


def lookup(name: str, *, timeout: float = 20.0) -> dict | None:
    """Return ``{vivino, image, url, match}`` for *name*, or ``None``.

    ``None`` means "not confident / unavailable" — the caller should keep the
    curated seed value. ``ratings`` count isn't returned because Vivino hydrates
    it client-side and it isn't present in the server-rendered HTML.
    """
    if requests is None:
        return None
    url = f"{_SEARCH}?q={urllib.parse.quote_plus(_clean_query(name))}"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code != 200:
            return None
        card = _parse_first_card(resp.text)
        time.sleep(1.0)  # be polite between requests
    except Exception:
        return None
    if not card or not _is_confident(name, card["name"]):
        return None
    return {
        "vivino": card["vivino"],
        "image": card["image"],
        "url": card["url"] or f"{_SEARCH}?q={urllib.parse.quote_plus(name)}",
        "match": card["name"],
    }


# Backwards-compatible helper used by the orchestrator's live-scrape path.
def lookup_rating(name: str, *, timeout: float = 20.0) -> tuple[float, int] | None:
    res = lookup(name, timeout=timeout)
    return (res["vivino"], 0) if res else None
