const products = [
  {
    id: "cordyceps",
    name: "Cordyceps sinensis",
    category: "Medicinal",
    dzongkhag: "Bumthang",
    group: "Tang NWFP Group",
    price: 18500,
    unit: "kg",
    stock: 18,
    batch: "CORD-2026-TG",
    status: "Published",
    document: "WCNP_Tang-NWFP.pdf",
    color: "linear-gradient(135deg, #244a3f, #9a6c24)",
    imagePos: "70% 52%",
    description: "High-value medicinal fungus collected under an approved management plan with batch-level stock tracking."
  },
  {
    id: "cane",
    name: "Himalayan Cane",
    category: "Craft",
    dzongkhag: "Trongsa",
    group: "Zangbi NWFP Group",
    price: 780,
    unit: "bundle",
    stock: 42,
    batch: "CAN-2026-ZB",
    status: "Review",
    document: "RMNP_Zangbi_NWFP.pdf",
    color: "linear-gradient(135deg, #2c648f, #6a8e53)",
    imagePos: "46% 68%",
    description: "Cane bundles for handicraft producers, linked to mapped collection zones and group permits."
  },
  {
    id: "daphne",
    name: "Daphne Bark",
    category: "Fiber",
    dzongkhag: "Trashigang",
    group: "Sakteng Lhayul Sangzey Deytshen",
    price: 1200,
    unit: "bundle",
    stock: 11,
    batch: "DAPH-2026-SK",
    status: "Draft",
    document: "SWS_Daphne Management Plan_Yumzang_Semthuen_NWFP.pdf",
    color: "linear-gradient(135deg, #6f5130, #1f6f5f)",
    imagePos: "58% 74%",
    description: "Daphne fiber harvested for traditional paper with officer validation pending."
  },
  {
    id: "mushroom",
    name: "Dried Wild Mushroom",
    category: "Food",
    dzongkhag: "Wangdue Phodrang",
    group: "Sephu NWFP Group",
    price: 1450,
    unit: "kg",
    stock: 26,
    batch: "MUSH-2026-SP",
    status: "Published",
    document: "WCNP_Sephu-NWFP.pdf",
    color: "linear-gradient(135deg, #7b4c32, #bf8426)",
    imagePos: "82% 64%",
    description: "Sorted dried mushrooms with origin details, group registry, and dispatch workflow."
  }
];

const sites = [
  { id: "tang", group: "Tang NWFP Group", dzongkhag: "Bumthang", product: "Cordyceps sinensis", status: "active", x: 47, y: 38 },
  { id: "zangbi", group: "Zangbi NWFP Group", dzongkhag: "Trongsa", product: "Himalayan Cane", status: "review", x: 39, y: 52 },
  { id: "sakteng", group: "Sakteng Lhayul Sangzey Deytshen", dzongkhag: "Trashigang", product: "Daphne Bark", status: "review", x: 73, y: 43 },
  { id: "sephu", group: "Sephu NWFP Group", dzongkhag: "Wangdue Phodrang", product: "Dried Wild Mushroom", status: "active", x: 32, y: 62 }
];

const downloads = [
  {
    title: "Sample Products CSV",
    type: "CSV",
    detail: "Product, group, batch, price, stock, status, and coordinates.",
    href: "downloads/sample-products.csv"
  },
  {
    title: "Resource Sites GeoJSON",
    type: "GeoJSON",
    detail: "Point features for marketplace origin and map display.",
    href: "downloads/sample-resource-sites.geojson"
  },
  {
    title: "Resource Sites Shapefile",
    type: "SHP ZIP",
    detail: "QGIS/ArcGIS compatible sample shapefile package.",
    href: "downloads/sample-resource-sites-shapefile.zip"
  },
  {
    title: "Plan Summary",
    type: "Markdown",
    detail: "Public-facing sample plan summary linked to a product batch.",
    href: "downloads/sample-plan-summary.md"
  },
  {
    title: "Marketplace Hero Photo",
    type: "PNG",
    detail: "Generated product table image used by the prototype hero and cards.",
    href: "assets/nwfp-hero.png"
  },
  {
    title: "Fallback Forest Image",
    type: "SVG",
    detail: "Lightweight backup visual asset.",
    href: "assets/forest-market.svg"
  },
  {
    title: "PWA App Icon",
    type: "SVG",
    detail: "Installable app icon asset.",
    href: "assets/icon.svg"
  },
  {
    title: "Tang Management Plan",
    type: "PDF",
    detail: "Existing sample PDF from the workspace management plans.",
    href: "../management_plans_nwfp/WCNP_Tang-NWFP.pdf"
  },
  {
    title: "Zangbi Management Plan",
    type: "PDF",
    detail: "Existing sample PDF from the workspace management plans.",
    href: "../management_plans_nwfp/RMNP_Zangbi_NWFP.pdf"
  },
  {
    title: "Daphne Management Plan",
    type: "PDF",
    detail: "Existing sample PDF from the workspace management plans.",
    href: "../management_plans_nwfp/SWS_Daphne Management Plan_Yumzang_Semthuen_NWFP.pdf"
  }
];

const state = {
  filter: "All",
  query: "",
  cart: []
};

const formatter = new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0
});

const productGrid = document.querySelector("#productGrid");
const filterChips = document.querySelector("#filterChips");
const searchInput = document.querySelector("#searchInput");
const productDetail = document.querySelector("#productDetail");
const cartCount = document.querySelector("#cartCount");
const cartItems = document.querySelector("#cartItems");
const cartTotal = document.querySelector("#cartTotal");
const toast = document.querySelector("#toast");

function money(value) {
  return `Nu ${formatter.format(value)}`;
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2400);
}

function categories() {
  return ["All", ...new Set(products.map((product) => product.category))];
}

function renderChips() {
  filterChips.innerHTML = categories()
    .map((category) => `<button class="${state.filter === category ? "active" : ""}" data-filter="${category}">${category}</button>`)
    .join("");
}

function productMatches(product) {
  const query = state.query.trim().toLowerCase();
  const filterMatch = state.filter === "All" || product.category === state.filter;
  const queryMatch = !query || [product.name, product.group, product.dzongkhag, product.category]
    .join(" ")
    .toLowerCase()
    .includes(query);
  return filterMatch && queryMatch;
}

function renderProducts() {
  const visible = products.filter(productMatches);
  productGrid.innerHTML = visible.map((product) => `
    <article class="product-card">
      <button class="product-image" style="--image-bg: ${product.color}; --image-pos: ${product.imagePos}" data-detail="${product.id}">
        <span>${product.category}</span>
      </button>
      <div class="product-card-body">
        <div class="card-topline">
          <span>${product.dzongkhag}</span>
          <span class="status ${product.status === "Published" ? "ok" : "warn"}">${product.status}</span>
        </div>
        <h3>${product.name}</h3>
        <div class="meta">${product.group}<br>${product.batch} · ${product.stock} ${product.unit}</div>
        <div class="price-line">
          <strong>${money(product.price)} <span>/ ${product.unit}</span></strong>
          <button class="small-button" data-add="${product.id}">Add</button>
        </div>
      </div>
    </article>
  `).join("") || `<p class="meta">No matching products found.</p>`;
}

function renderDetail(product) {
  productDetail.hidden = false;
  productDetail.innerHTML = `
    <article class="detail-card">
      <div class="detail-hero" style="--image-bg: ${product.color}; --image-pos: ${product.imagePos}">
        <div>
          <p class="eyebrow">${product.category} · ${product.status}</p>
          <h2>${product.name}</h2>
        </div>
      </div>
      <div class="detail-body">
        <div>
          <p class="eyebrow">Traceable product origin</p>
          <p>${product.description}</p>
        </div>
        <div class="fact-grid">
          <div><span>Group</span><strong>${product.group}</strong></div>
          <div><span>Dzongkhag</span><strong>${product.dzongkhag}</strong></div>
          <div><span>Batch</span><strong>${product.batch}</strong></div>
          <div><span>Document</span><strong>${product.document}</strong></div>
        </div>
        <div class="price-line">
          <strong>${money(product.price)} / ${product.unit}</strong>
          <button class="primary-button" data-add="${product.id}">Add to Cart</button>
        </div>
      </div>
    </article>
  `;
  productDetail.scrollIntoView({ behavior: "smooth", block: "start" });
}

function addToCart(productId) {
  const product = products.find((item) => item.id === productId);
  const existing = state.cart.find((item) => item.id === productId);
  if (existing) {
    if (existing.quantity >= product.stock) {
      showToast(`Only ${product.stock} ${product.unit} available`);
      return;
    }
    existing.quantity += 1;
  } else {
    state.cart.push({ ...product, quantity: 1 });
  }
  renderCart();
  showToast(`${product.name} added to cart`);
}

function renderCart() {
  const count = state.cart.reduce((total, item) => total + item.quantity, 0);
  const total = state.cart.reduce((sum, item) => sum + item.quantity * item.price, 0);
  cartCount.textContent = count;
  cartTotal.textContent = money(total);
  cartItems.innerHTML = state.cart.map((item) => `
    <div class="cart-row">
      <div>
        <strong>${item.name}</strong>
        <div class="meta">${item.group} · ${item.batch}</div>
      </div>
      <div><strong>${item.quantity} x</strong> ${money(item.price)}</div>
    </div>
  `).join("") || `<p class="meta">Your cart is empty.</p>`;
}

function renderMap() {
  const filter = document.querySelector("#mapFilter").value;
  const mapCanvas = document.querySelector("#mapCanvas");
  const visibleSites = sites.filter((site) => filter === "all" || site.status === filter);
  mapCanvas.innerHTML = `
    <span class="map-label map-label-n">Northern parks</span>
    <span class="map-label map-label-s">Southern divisions</span>
    ${visibleSites.map((site) => `
      <button class="marker ${site.status}" style="left: ${site.x}%; top: ${site.y}%;" data-site="${site.id}" title="${site.group}"></button>
    `).join("")}
  `;
}

function renderDownloads() {
  document.querySelector("#downloadGrid").innerHTML = downloads.map((item) => `
    <article class="download-card">
      <header>
        <div>
          <h3>${item.title}</h3>
          <div class="meta">${item.type}</div>
        </div>
        <span class="status ok">Ready</span>
      </header>
      <p class="meta">${item.detail}</p>
      <footer>
        <a class="primary-button" href="${item.href}" download>Download</a>
        <a class="text-button" href="${item.href}" target="_blank" rel="noreferrer">Open</a>
      </footer>
    </article>
  `).join("");
}

function showView(view) {
  if (view === "cart") {
    document.querySelector("#cart").hidden = false;
    document.querySelector("#cart").scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }

  document.querySelector("#cart").hidden = true;

  document.querySelectorAll(".bottom-nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });

  const target = view === "market" ? document.querySelector("#market") : document.querySelector(`#${view}`);
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

document.addEventListener("click", (event) => {
  const filter = event.target.closest("[data-filter]");
  const add = event.target.closest("[data-add]");
  const detail = event.target.closest("[data-detail]");
  const nav = event.target.closest("[data-view]");
  const siteMarker = event.target.closest("[data-site]");
  const fakeAction = event.target.closest("[data-fake-action]");

  if (filter) {
    state.filter = filter.dataset.filter;
    renderChips();
    renderProducts();
  }

  if (add) {
    addToCart(add.dataset.add);
  }

  if (detail) {
    renderDetail(products.find((product) => product.id === detail.dataset.detail));
  }

  if (nav) {
    showView(nav.dataset.view);
  }

  if (siteMarker) {
    const site = sites.find((item) => item.id === siteMarker.dataset.site);
    document.querySelector("#mapPanel").innerHTML = `
      <p class="eyebrow">${site.status === "active" ? "Active group" : "Needs review"}</p>
      <h3>${site.group}</h3>
      <p>${site.product} origin in ${site.dzongkhag}. Linked boundary and resource site layers are represented here for the prototype.</p>
    `;
  }

  if (fakeAction) {
    showToast(`${fakeAction.dataset.fakeAction} queued for Django workflow`);
  }

});

searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderProducts();
});

document.querySelector("#clearSearch").addEventListener("click", () => {
  state.query = "";
  searchInput.value = "";
  renderProducts();
});

document.querySelector("#mapFilter").addEventListener("change", renderMap);

document.querySelector("#checkoutButton").addEventListener("click", () => {
  if (!state.cart.length) {
    showToast("Add at least one product before checkout");
    return;
  }
  state.cart = [];
  renderCart();
  showToast("Manual order submitted for seller confirmation");
});

document.querySelector("#addProductButton").addEventListener("click", () => {
  showToast("Product form prototype: images, price, batch, documents");
});

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  const installButton = document.querySelector("#installButton");
  installButton.hidden = false;
  installButton.addEventListener("click", async () => {
    installButton.hidden = true;
    event.prompt();
    await event.userChoice;
  }, { once: true });
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js");
  });
}

renderChips();
renderProducts();
renderCart();
renderMap();
renderDownloads();
