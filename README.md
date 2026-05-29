# Pour Decisions 🍷

The best wines in UK supermarkets, **ranked by their average [Vivino](https://www.vivino.com) score**.
Aesthetically simple, a little bit playful — make better *pour decisions*.

Covers **Waitrose, M&S, Ocado, Aldi, Lidl, Tesco and Sainsbury's**, filterable by
shop and by style (red / white / rosé / sparkling), showing each bottle, its name,
price and average Vivino score. Shows the **top 25** of whatever you've filtered to.

## How it works

The project is split into two halves that meet at a single data file:

```
┌─ scripts/  (fortnightly job) ──────────────┐      ┌─ frontend (static) ───┐
│ scrape each supermarket's wine listings    │      │ index.html            │
│ → enrich each bottle with its Vivino score │ ──▶  │ assets/styles.css     │
│ → rank by score → write data/wines.json    │      │ assets/app.js         │
└────────────────────────────────────────────┘      └───────────────────────┘
                         data/wines.json  ◀── the contract between the two
```

- **Frontend** — plain HTML/CSS/JS, no build step. It fetches `data/wines.json`,
  renders the filter chips, ranks by Vivino score and shows the top 25. Wine
  bottles are drawn as inline SVGs tinted by wine type, so there are no external
  image dependencies.
- **Scraper** (`scripts/`) — one scraper per supermarket plus a Vivino rating
  resolver, orchestrated by `scripts/update_wines.py`.

## Running locally

It's a static site — serve the folder with anything:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploying

`.github/workflows/deploy.yml` publishes the site to **GitHub Pages** on every
push to `main`. Enable it once under *Settings → Pages → Build and deployment →
Source: GitHub Actions*. No build step — the repo root is the site.

## Refreshing the wine list

```bash
pip install -r requirements.txt

python scripts/update_wines.py          # full run: curated catalog + live Vivino enrichment
python scripts/update_wines.py --seed   # curated data only, no network
```

This (re)generates `data/wines.json`, sorted by Vivino score with metadata
(`generated_at`, `next_update`, the list of `live_sources`, etc.).

### Fortnightly updates

`.github/workflows/update-wines.yml` runs the refresh on the **1st and 15th of
each month** (≈ fortnightly) and commits `data/wines.json` if anything changed.
You can also run it on demand from the Actions tab.

## About the data

There are two different data sources, handled differently because they behave
very differently in practice:

**Vivino scores + bottle photos — fetched live.** `scripts/scrapers/vivino.py`
queries Vivino's server-rendered search and reads the average community score,
the canonical wine name and a real bottle-shot image. The hard part is
*matching*: supermarket own-label wines ("Tesco Finest Barolo") have no Vivino
page, so a naive search returns some unrelated wine. To avoid silently
corrupting a *ranking* app, a confident match is required — a real
producer/brand token must appear in the result, not just a shared grape,
region or range word. When the match isn't confident the bottle keeps its
curated score and a drawn SVG bottle. In the shipped `data/wines.json` the
genuinely branded bottles (Cloudy Bay, Catena, Whispering Angel, Fontanafredda,
Mirabeau, Bottega, 19 Crimes, …) carry **live Vivino scores and real photos**,
flagged with `vivino_verified` and a ✓ in the UI.

**Supermarket catalogs — curated.** Waitrose, Tesco, Sainsbury's, Aldi et al.
serve JavaScript single-page apps behind bot protection, so the product list and
prices can't be pulled with a plain HTTP request. The scrapers in
`scripts/scrapers/supermarkets.py` carry each retailer's real listing URLs and
product-card selectors and are ready for a browser-based runner (e.g.
Playwright), but until that's wired up the catalog falls back to the curated
list in `scripts/wines_seed.py`. The Vivino enrichment above still runs on top
of it, so scores and photos are live even while the catalog is curated.

> Scores are from the Vivino community; prices and availability change, so check
> the shop before buying. Pour Decisions is independent and not affiliated with
> any supermarket or with Vivino.
