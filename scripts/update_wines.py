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
    """Return (wines, supermarkets_done_live)."""
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
                rating = vivino.lookup_rating(w["name"])
                if rating is None:
                    continue  # no Vivino score -> can't rank it, skip
                w["vivino"], w["ratings"] = rating
                w.setdefault("region", "")
                w.setdefault("grape", "")
                w.setdefault("url", "#")
                w["id"] = _slug(w["supermarket"], w["name"])
                wines.append(w)
            live.add(result.supermarket)
    return wines, live


def build(seed_only: bool = False, verbose: bool = True) -> dict:
    seed = get_seed_wines()
    if seed_only:
        wines = seed
        live: set[str] = set()
    else:
        live_wines, live = scrape_live(verbose=verbose)
        # Fill in supermarkets that didn't scrape with their seed bottles.
        wines = live_wines + [w for w in seed if w["supermarket"] not in live]

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
        live = ", ".join(data["live_sources"]) or "none (used seed data)"
        print(f"\nWrote {data['count']} wines to {OUT.relative_to(ROOT)}")
        print(f"Live-scraped sources: {live}")
        print(f"Next update due: {data['next_update']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
