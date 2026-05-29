/* Pour Decisions — loads the ranked wine list and powers the filters. */

const TOP_N = 25;

const TYPE_LABELS = {
  red: "Red",
  white: "White",
  rose: "Rosé",
  sparkling: "Sparkling",
};

// Liquid colours for the SVG bottle, by wine type.
const BOTTLE_COLOURS = {
  red: { glass: "#3a5a40", liquid: "#7b1733" },
  white: { glass: "#cdd6b5", liquid: "#e8d68a" },
  rose: { glass: "#d9c2c2", liquid: "#f3a9bd" },
  sparkling: { glass: "#3a4a40", liquid: "#e6cf86" },
};

const state = {
  wines: [],
  shop: "All",
  type: "All",
};

const el = {
  meta: document.getElementById("meta"),
  shopChips: document.getElementById("shop-chips"),
  typeChips: document.getElementById("type-chips"),
  grid: document.getElementById("grid"),
  note: document.getElementById("results-note"),
  empty: document.getElementById("empty"),
};

init();

async function init() {
  try {
    const res = await fetch("data/wines.json", { cache: "no-cache" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.wines = data.wines || [];
    renderMeta(data);
    renderChips(el.shopChips, "shop", ["All", ...(data.supermarkets || [])]);
    renderChips(
      el.typeChips,
      "type",
      ["All", ...(data.types || [])],
      (v) => (v === "All" ? "All" : TYPE_LABELS[v] || v)
    );
    render();
  } catch (err) {
    el.grid.innerHTML = "";
    el.empty.hidden = false;
    el.empty.textContent = "Couldn't pour the list right now. Refresh in a moment. 🍷";
    console.error(err);
  }
}

function renderMeta(data) {
  const fmt = (d) =>
    new Date(d + "T00:00:00").toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  const verified = data.vivino_verified
    ? ` · ${data.vivino_verified} scores ✓ live from Vivino`
    : "";
  el.meta.textContent =
    `Updated ${fmt(data.generated_at)} · next pour ${fmt(data.next_update)} · ${data.count} bottles${verified}`;
}

function renderChips(container, key, values, labelFn = (v) => v) {
  container.innerHTML = "";
  values.forEach((value) => {
    const btn = document.createElement("button");
    btn.className = "chip";
    btn.type = "button";
    btn.textContent = labelFn(value);
    btn.setAttribute("aria-pressed", String(state[key] === value));
    btn.addEventListener("click", () => {
      state[key] = value;
      [...container.children].forEach((c) =>
        c.setAttribute("aria-pressed", String(c === btn))
      );
      render();
    });
    container.appendChild(btn);
  });
}

function render() {
  const filtered = state.wines.filter(
    (w) =>
      (state.shop === "All" || w.supermarket === state.shop) &&
      (state.type === "All" || w.type === state.type)
  );
  // wines.json is pre-sorted by Vivino score, but sort defensively anyway.
  filtered.sort((a, b) => b.vivino - a.vivino || b.ratings - a.ratings);
  const top = filtered.slice(0, TOP_N);

  el.note.textContent = top.length
    ? `Top ${top.length} ${describe()} by average Vivino score`
    : "";
  el.empty.hidden = top.length > 0;
  el.grid.innerHTML = top.map(cardHTML).join("");
}

function describe() {
  const type =
    state.type === "All" ? "wines" : `${(TYPE_LABELS[state.type] || state.type).toLowerCase()} wines`;
  const shop = state.shop === "All" ? "across all shops" : `at ${state.shop}`;
  return `${type} ${shop}`;
}

function cardHTML(w) {
  const bottle = w.image
    ? `<img class="card__photo" src="${escape(w.image)}" alt="${escape(w.name)} bottle"
           loading="lazy" referrerpolicy="no-referrer"
           onerror="this.outerHTML=window.__bottleSVG('${w.type}')" />`
    : bottleSVG(w.type);

  const scoreInner = `<span class="star">★</span>${Number(w.vivino).toFixed(1)}${
    w.vivino_verified ? '<span class="verified" title="Verified live on Vivino">✓</span>' : ""
  }`;
  const score = w.vivino_url
    ? `<a class="score" href="${escape(w.vivino_url)}" target="_blank" rel="noopener noreferrer"
          title="View on Vivino">${scoreInner}</a>`
    : `<span class="score">${scoreInner}</span>`;

  return `
    <li class="card">
      <div class="card__bottle">${bottle}</div>
      <div class="card__body">
        <span class="card__shop">${escape(w.supermarket)}</span>
        <h3 class="card__name">
          <a href="${escape(w.url)}" target="_blank" rel="noopener noreferrer">${escape(w.name)}</a>
        </h3>
        <p class="card__sub">${escape(w.region || "")}${w.grape ? " · " + escape(w.grape) : ""}</p>
        <span class="type-tag type-${w.type}">${TYPE_LABELS[w.type] || w.type}</span>
        <div class="card__foot">
          <span class="price">£${Number(w.price).toFixed(2)}</span>
          ${score}
        </div>
      </div>
    </li>`;
}

// Exposed so an <img> onerror can swap a broken photo for the SVG fallback.
window.__bottleSVG = bottleSVG;

function bottleSVG(type) {
  const c = BOTTLE_COLOURS[type] || BOTTLE_COLOURS.red;
  return `
    <svg viewBox="0 0 40 100" role="img" aria-label="${TYPE_LABELS[type] || type} wine bottle">
      <defs>
        <clipPath id="b-${type}">
          <path d="M16 6h8v18c0 3 6 6 6 16v46a4 4 0 0 1-4 4H14a4 4 0 0 1-4-4V40c0-10 6-13 6-16V6z"/>
        </clipPath>
      </defs>
      <path d="M16 6h8v18c0 3 6 6 6 16v46a4 4 0 0 1-4 4H14a4 4 0 0 1-4-4V40c0-10 6-13 6-16V6z"
            fill="${c.glass}" stroke="rgba(0,0,0,0.18)" stroke-width="1"/>
      <rect x="10" y="58" width="20" height="36" fill="${c.liquid}" clip-path="url(#b-${type})"/>
      <rect x="15" y="2" width="10" height="6" rx="1.5" fill="#caa46a"/>
      <rect x="11" y="62" width="18" height="16" fill="#fff" opacity="0.92" clip-path="url(#b-${type})"/>
      <line x1="20" y1="14" x2="20" y2="58" stroke="rgba(255,255,255,0.25)" stroke-width="3" stroke-linecap="round"/>
    </svg>`;
}

function formatCount(n) {
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
  return String(n);
}

function escape(s) {
  return String(s ?? "").replace(/[&<>"']/g, (m) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m])
  );
}
