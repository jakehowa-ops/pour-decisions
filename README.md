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

## Refreshing the wine list

```bash
pip install -r requirements.txt

python scripts/update_wines.py          # full run: tries a live scrape, falls back to seed
python scripts/update_wines.py --seed   # curated seed data only, no network
```

This (re)generates `data/wines.json`, sorted by Vivino score with metadata
(`generated_at`, `next_update`, the list of `live_sources`, etc.).

### Fortnightly updates

`.github/workflows/update-wines.yml` runs the refresh on the **1st and 15th of
each month** (≈ fortnightly) and commits `data/wines.json` if anything changed.
You can also run it on demand from the Actions tab.

## About the data

Supermarket sites and Vivino actively defend against automated crawling, and a
live scrape needs outbound network access. The scrapers in `scripts/scrapers/`
carry each retailer's real listing URLs and product-card selectors, but when a
site can't be reached (CI without egress, bot protection, markup changes) the
pipeline **falls back to the curated dataset in `scripts/wines_seed.py`** so the
app always has a complete, sensible top-25 to show. That seed is what ships in
`data/wines.json` today.

> Scores are from the Vivino community; prices and availability change, so check
> the shop before buying. Pour Decisions is independent and not affiliated with
> any supermarket or with Vivino.
