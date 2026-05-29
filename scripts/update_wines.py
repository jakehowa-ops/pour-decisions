#!/usr/bin/env python3
"""Refresh the Pour Decisions wine list.

Pipeline
--------
1. Run every supermarket scraper (Waitrose, M&S, Ocado, Aldi, Lidl, Tesco,
   Sainsbury's).
2. Enrich each scraped bottle with its average Vivino score.
3. For any supermarket that couldn't be scraped (bot defences / no network),
   fall back to the curated seed dataset so the app always has data.
4. Sort by Vivino score and write ``data/wines.json`` with metadata.

This is what the fortnightly GitHub Action runs. Locally:

    python scripts/update_wines.py            # full run (tries live scrape)
    python scripts/update_wines.py --seed     # seed only, no network
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scrapers import SCRAPERS  # noqa: E402
from scrapers import vivino  # noqa: E402
from wines_seed import SUPERMARKETS, WINE_TYPES, get_seed_wines  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "wines.json"
UPDATE_INTERVAL_DAYS = 14  # fortnightly


def _slug(*parts: str) -> str:
    import re

    s = "-".join(parts).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def scrape_live(verbose: bool = True) -> tuple[list[dict], set[str]]:
    """Return (raw_scraped_wines, supermarkets_done_live).

    Scraped bottles have no Vivino score yet — :func:`enrich` adds that.
    """
    wines: list[dict] = []
    live: set[str] = set()
    for cls in SCRAPERS:
        scraper = cls()
        result = scraper.scrape()
        if verbose:
            status = "ok" if result.ok else f"fallback ({result.error})"
            print(f"  {result.supermarket:<14} {len(result.wines):>3} bottles  [{status}]")
        if result.ok and result.wines:
            for w in result.wines:
                w.setdefault("region", "")
                w.setdefault("grape", "")
                w.setdefault("ratings", 0)
                w["id"] = _slug(w["supermarket"], w["name"])
                w["url"] = w.get("url") or "#"
                wines.append(w)
            live.add(result.supermarket)
    return wines, live


def enrich(wines: list[dict], verbose: bool = True) -> list[dict]:
    """Attach live Vivino data (score, bottle photo, link) when confident.

    Each wine keeps its curated/seed Vivino score as a fallback. A confident
    match overwrites the score, adds a real bottle-shot image and a Vivino link,
    and flags ``vivino_verified``. Bottles with neither a confident match nor a
    pre-existing score are dropped (they can't be ranked).
    """
    out: list[dict] = []
    hits = 0
    for w in wines:
        res = vivino.lookup(w["name"])
        if res:
            w["vivino"] = res["vivino"]
            w["image"] = res["image"]
            w["vivino_url"] = res["url"]
            w["vivino_match"] = res["match"]
            w["vivino_verified"] = True
            hits += 1
        else:
            w.setdefault("image", None)
            w.setdefault("vivino_url", None)
            w.setdefault("vivino_verified", False)
        if w.get("vivino") is not None:
            out.append(w)
    if verbose:
        print(f"  Vivino: {hits}/{len(wines)} bottles verified live")
    return out


def build(seed_only: bool = False, verbose: bool = True) -> dict:
    seed = get_seed_wines()
    if seed_only:
        for w in seed:
            w.setdefault("image", None)
            w.setdefault("vivino_url", None)
            w.setdefault("vivino_verified", False)
        wines = seed
        live: set[str] = set()
    else:
        live_wines, live = scrape_live(verbose=verbose)
        # Fill in supermarkets that didn't scrape with their seed bottles.
        merged = live_wines + [w for w in seed if w["supermarket"] not in live]
        wines = enrich(merged, verbose=verbose)

    # Rank: highest Vivino first, ties broken by number of ratings.
    wines.sort(key=lambda w: (w["vivino"], w["ratings"]), reverse=True)

    now = dt.datetime.now(dt.timezone.utc)
    nxt = now + dt.timedelta(days=UPDATE_INTERVAL_DAYS)
    return {
        "generated_at": now.strftime("%Y-%m-%d"),
        "next_update": nxt.strftime("%Y-%m-%d"),
        "update_interval_days": UPDATE_INTERVAL_DAYS,
        "supermarkets": SUPERMARKETS,
        "types": WINE_TYPES,
        "live_sources": sorted(live),
        "vivino_verified": sum(1 for w in wines if w.get("vivino_verified")),
        "count": len(wines),
        "wines": wines,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh the Pour Decisions wine list.")
    ap.add_argument("--seed", action="store_true", help="use curated seed data only (no network)")
    ap.add_argument("--quiet", action="store_true", help="suppress progress output")
    args = ap.parse_args()

    verbose = not args.quiet
    if verbose:
        print("Pouring over the shelves...")

    data = build(seed_only=args.seed, verbose=verbose)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if verbose:
        live = ", ".join(data["live_sources"]) or "none (supermarket catalogs use curated list)"
        print(f"\nWrote {data['count']} wines to {OUT.relative_to(ROOT)}")
        print(f"Live-scraped catalogs: {live}")
        print(f"Vivino scores verified live: {data['vivino_verified']}/{data['count']}")
        print(f"Next update due: {data['next_update']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
