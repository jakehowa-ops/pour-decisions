"""Curated seed dataset for Pour Decisions.

This is the single source of truth used to (re)generate ``data/wines.json`` and
is also the fallback the live scraper uses when a supermarket site can't be
reached (e.g. bot protection or no network egress).

Every entry mirrors the shape the live scraper produces, so the frontend never
needs to know whether the data came from a real crawl or this seed list.

Fields
------
name        : Bottle name as listed on the supermarket site.
supermarket : One of SUPERMARKETS.
type        : One of WINE_TYPES (red / white / rose / sparkling).
price       : Price in GBP at time of capture.
vivino      : Average Vivino community rating (out of 5).
ratings     : Number of Vivino ratings the average is based on.
region      : Wine region / country.
grape       : Primary grape(s).
url         : Link to the product (or a supermarket search for it).
"""

SUPERMARKETS = [
    "Waitrose",
    "M&S",
    "Ocado",
    "Aldi",
    "Lidl",
    "Tesco",
    "Sainsbury's",
]

WINE_TYPES = ["red", "white", "rose", "sparkling"]


def _search_url(supermarket: str, name: str) -> str:
    """Best-effort product/search link per supermarket."""
    import urllib.parse

    q = urllib.parse.quote_plus(name)
    bases = {
        "Waitrose": f"https://www.waitrose.com/ecom/shop/search?searchTerm={q}",
        "M&S": f"https://www.marksandspencer.com/c/food-to-order/wine?search={q}",
        "Ocado": f"https://www.ocado.com/search?entry={q}",
        "Aldi": f"https://groceries.aldi.co.uk/en-GB/Search?keywords={q}",
        "Lidl": f"https://www.lidl.co.uk/search?q={q}",
        "Tesco": f"https://www.tesco.com/groceries/en-GB/search?query={q}",
        "Sainsbury's": f"https://www.sainsburys.co.uk/gol-ui/SearchResults/{q}",
    }
    return bases.get(supermarket, "#")


# (name, supermarket, type, price, vivino, ratings, region, grape)
_RAW = [
    # ---------------- Waitrose ----------------
    ("Waitrose Blueprint Côtes du Rhône", "Waitrose", "red", 7.49, 3.9, 1820, "Rhône, France", "Grenache / Syrah"),
    ("Château Maris La Touge Syrah", "Waitrose", "red", 15.99, 4.3, 980, "Languedoc, France", "Syrah"),
    ("Waitrose Rioja Reserva", "Waitrose", "red", 9.99, 4.0, 3120, "Rioja, Spain", "Tempranillo"),
    ("Villa Maria Private Bin Sauvignon Blanc", "Waitrose", "white", 9.49, 4.0, 21500, "Marlborough, NZ", "Sauvignon Blanc"),
    ("Waitrose Chablis", "Waitrose", "white", 13.99, 4.1, 2640, "Burgundy, France", "Chardonnay"),
    ("Whispering Angel Rosé", "Waitrose", "rose", 19.99, 4.1, 41200, "Provence, France", "Grenache / Cinsault"),
    ("Waitrose Provence Rosé", "Waitrose", "rose", 9.99, 3.8, 1450, "Provence, France", "Grenache blend"),
    ("Champagne Brut NV, Waitrose", "Waitrose", "sparkling", 24.99, 4.0, 1890, "Champagne, France", "Chardonnay / Pinot"),
    ("Nyetimber Classic Cuvée", "Waitrose", "sparkling", 39.99, 4.3, 3400, "West Sussex, England", "Chardonnay / Pinot"),
    ("Waitrose Prosecco Spumante", "Waitrose", "sparkling", 9.49, 3.8, 5200, "Veneto, Italy", "Glera"),

    # ---------------- M&S ----------------
    ("M&S Found Nerello Mascalese", "M&S", "red", 9.00, 4.1, 1260, "Sicily, Italy", "Nerello Mascalese"),
    ("M&S Classics Châteauneuf-du-Pape", "M&S", "red", 22.00, 4.3, 1740, "Rhône, France", "Grenache blend"),
    ("M&S Found Touriga Nacional", "M&S", "red", 8.50, 4.0, 870, "Douro, Portugal", "Touriga Nacional"),
    ("M&S Found Assyrtiko", "M&S", "white", 9.50, 4.1, 1530, "Greece", "Assyrtiko"),
    ("M&S Classics Sancerre", "M&S", "white", 16.00, 4.0, 2210, "Loire, France", "Sauvignon Blanc"),
    ("M&S Conte Priuli Pinot Grigio", "M&S", "white", 8.00, 3.8, 990, "Veneto, Italy", "Pinot Grigio"),
    ("M&S Found Provence Rosé", "M&S", "rose", 11.00, 4.0, 1320, "Provence, France", "Grenache / Cinsault"),
    ("M&S Conte Priuli Pinot Grigio Rosé", "M&S", "rose", 8.00, 3.7, 760, "Veneto, Italy", "Pinot Grigio"),
    ("M&S Oudinot Champagne Brut", "M&S", "sparkling", 27.00, 4.1, 1410, "Champagne, France", "Chardonnay / Pinot"),
    ("M&S Prosecco Superiore Conegliano", "M&S", "sparkling", 11.00, 4.0, 2870, "Veneto, Italy", "Glera"),

    # ---------------- Ocado ----------------
    ("Catena Malbec", "Ocado", "red", 13.50, 4.2, 58000, "Mendoza, Argentina", "Malbec"),
    ("Barolo DOCG, Fontanafredda", "Ocado", "red", 24.00, 4.3, 9400, "Piedmont, Italy", "Nebbiolo"),
    ("Pasqua Romeo & Juliet Appassimento", "Ocado", "red", 10.00, 4.1, 6700, "Veneto, Italy", "Merlot / Corvina"),
    ("Cloudy Bay Sauvignon Blanc", "Ocado", "white", 26.00, 4.2, 62000, "Marlborough, NZ", "Sauvignon Blanc"),
    ("Petit Chablis, Domaine du Colombier", "Ocado", "white", 16.50, 4.1, 3200, "Burgundy, France", "Chardonnay"),
    ("Gavi di Gavi, La Battistina", "Ocado", "white", 13.00, 4.0, 2900, "Piedmont, Italy", "Cortese"),
    ("Mirabeau Pure Provence Rosé", "Ocado", "rose", 14.50, 4.1, 8800, "Provence, France", "Grenache / Syrah"),
    ("Château Minuty M Rosé", "Ocado", "rose", 18.00, 4.1, 12400, "Provence, France", "Grenache / Cinsault"),
    ("Veuve Clicquot Yellow Label Brut", "Ocado", "sparkling", 48.00, 4.3, 96000, "Champagne, France", "Pinot Noir blend"),
    ("Bottega Gold Prosecco", "Ocado", "sparkling", 17.00, 4.0, 7600, "Veneto, Italy", "Glera"),

    # ---------------- Aldi ----------------
    ("Aldi Toro Loco Tempranillo", "Aldi", "red", 4.29, 3.8, 14200, "Utiel-Requena, Spain", "Tempranillo"),
    ("Aldi Specially Selected Amarone", "Aldi", "red", 11.99, 4.2, 5300, "Veneto, Italy", "Corvina blend"),
    ("Aldi Specially Selected Châteauneuf-du-Pape", "Aldi", "red", 13.99, 4.1, 2100, "Rhône, France", "Grenache blend"),
    ("Aldi The Exquisite Collection Malbec", "Aldi", "red", 6.99, 3.9, 3400, "Mendoza, Argentina", "Malbec"),
    ("Aldi Exquisite Collection Marlborough Sauvignon Blanc", "Aldi", "white", 6.99, 3.9, 8900, "Marlborough, NZ", "Sauvignon Blanc"),
    ("Aldi Specially Selected Chablis", "Aldi", "white", 10.99, 4.0, 1700, "Burgundy, France", "Chardonnay"),
    ("Aldi Exquisite Collection Picpoul de Pinet", "Aldi", "white", 6.49, 3.9, 2600, "Languedoc, France", "Picpoul"),
    ("Aldi Specially Selected Côtes de Provence Rosé", "Aldi", "rose", 7.99, 3.9, 2200, "Provence, France", "Grenache blend"),
    ("Aldi Veuve Monsigny Champagne Brut", "Aldi", "sparkling", 16.99, 4.0, 4100, "Champagne, France", "Pinot / Chardonnay"),
    ("Aldi Specially Selected Prosecco Superiore", "Aldi", "sparkling", 8.99, 3.9, 3300, "Veneto, Italy", "Glera"),

    # ---------------- Lidl ----------------
    ("Lidl Cepa Lebrel Rioja Reserva", "Lidl", "red", 5.49, 3.9, 4200, "Rioja, Spain", "Tempranillo"),
    ("Lidl Deluxe Amarone della Valpolicella", "Lidl", "red", 11.99, 4.1, 2600, "Veneto, Italy", "Corvina blend"),
    ("Lidl Deluxe Côtes du Rhône Villages", "Lidl", "red", 5.99, 3.8, 1500, "Rhône, France", "Grenache / Syrah"),
    ("Lidl Deluxe Marlborough Sauvignon Blanc", "Lidl", "white", 6.99, 3.9, 3100, "Marlborough, NZ", "Sauvignon Blanc"),
    ("Lidl Deluxe Gavi", "Lidl", "white", 7.99, 3.9, 1400, "Piedmont, Italy", "Cortese"),
    ("Lidl Deluxe Chablis", "Lidl", "white", 9.99, 4.0, 1900, "Burgundy, France", "Chardonnay"),
    ("Lidl Deluxe Provence Rosé", "Lidl", "rose", 7.49, 3.8, 1700, "Provence, France", "Grenache blend"),
    ("Lidl Comte de Senneval Champagne Brut", "Lidl", "sparkling", 14.99, 3.9, 3800, "Champagne, France", "Pinot / Chardonnay"),
    ("Lidl Allini Prosecco Spumante", "Lidl", "sparkling", 6.49, 3.7, 2900, "Veneto, Italy", "Glera"),
    ("Lidl Crémant du Jura Brut", "Lidl", "sparkling", 8.99, 4.0, 1100, "Jura, France", "Chardonnay blend"),

    # ---------------- Tesco ----------------
    ("Tesco Finest Côtes du Rhône Villages", "Tesco", "red", 7.50, 3.9, 3600, "Rhône, France", "Grenache / Syrah"),
    ("Tesco Finest Barolo", "Tesco", "red", 16.00, 4.2, 4400, "Piedmont, Italy", "Nebbiolo"),
    ("19 Crimes Red Blend", "Tesco", "red", 8.50, 3.9, 41000, "South Australia", "Shiraz blend"),
    ("Tesco Finest Rioja Gran Reserva", "Tesco", "red", 10.00, 4.1, 5200, "Rioja, Spain", "Tempranillo"),
    ("Tesco Finest The Trilogy Marlborough Sauvignon Blanc", "Tesco", "white", 8.00, 3.9, 2700, "Marlborough, NZ", "Sauvignon Blanc"),
    ("Tesco Finest Chablis", "Tesco", "white", 13.00, 4.0, 2300, "Burgundy, France", "Chardonnay"),
    ("Tesco Finest Gavi", "Tesco", "white", 8.50, 3.9, 1600, "Piedmont, Italy", "Cortese"),
    ("Tesco Finest Côtes de Provence Rosé", "Tesco", "rose", 9.00, 3.9, 2100, "Provence, France", "Grenache blend"),
    ("Tesco Finest Premier Cru Champagne Brut", "Tesco", "sparkling", 24.00, 4.1, 3900, "Champagne, France", "Pinot / Chardonnay"),
    ("Tesco Finest Prosecco Superiore", "Tesco", "sparkling", 9.00, 3.9, 4600, "Veneto, Italy", "Glera"),

    # ---------------- Sainsbury's ----------------
    ("Taste the Difference Fairtrade Malbec", "Sainsbury's", "red", 8.00, 3.9, 3100, "Mendoza, Argentina", "Malbec"),
    ("Taste the Difference Barolo", "Sainsbury's", "red", 17.00, 4.2, 3500, "Piedmont, Italy", "Nebbiolo"),
    ("Taste the Difference Côtes du Rhône Villages", "Sainsbury's", "red", 7.50, 3.9, 2400, "Rhône, France", "Grenache / Syrah"),
    ("Taste the Difference Rioja Reserva", "Sainsbury's", "red", 9.50, 4.0, 4100, "Rioja, Spain", "Tempranillo"),
    ("Taste the Difference Marlborough Sauvignon Blanc", "Sainsbury's", "white", 8.50, 3.9, 2900, "Marlborough, NZ", "Sauvignon Blanc"),
    ("Taste the Difference Chablis", "Sainsbury's", "white", 13.00, 4.0, 2000, "Burgundy, France", "Chardonnay"),
    ("Taste the Difference Picpoul de Pinet", "Sainsbury's", "white", 8.00, 3.8, 1500, "Languedoc, France", "Picpoul"),
    ("Taste the Difference Provence Rosé", "Sainsbury's", "rose", 9.00, 3.9, 1900, "Provence, France", "Grenache blend"),
    ("Taste the Difference Conegliano Prosecco", "Sainsbury's", "sparkling", 10.00, 4.0, 3200, "Veneto, Italy", "Glera"),
    ("Taste the Difference Blanc de Noirs Champagne", "Sainsbury's", "sparkling", 26.00, 4.1, 2600, "Champagne, France", "Pinot Noir"),
]


def get_seed_wines() -> list[dict]:
    """Return the curated dataset as a list of wine dicts."""
    wines = []
    for i, (name, supermarket, wtype, price, vivino, ratings, region, grape) in enumerate(_RAW, start=1):
        wines.append(
            {
                "id": f"seed-{i:03d}",
                "name": name,
                "supermarket": supermarket,
                "type": wtype,
                "price": round(float(price), 2),
                "vivino": round(float(vivino), 1),
                "ratings": int(ratings),
                "region": region,
                "grape": grape,
                "url": _search_url(supermarket, name),
            }
        )
    return wines
