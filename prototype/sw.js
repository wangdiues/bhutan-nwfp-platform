const CACHE_NAME = "bhutan-nwfp-prototype-v5";
const ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./management.html",
  "./management.css",
  "./management.js",
  "./manifest.webmanifest",
  "./assets/icon.svg",
  "./assets/nwfp-hero.png",
  "./assets/nwfp-management-groups-bhutan.jpeg",
  "./assets/forest-market.svg",
  "./downloads/national-nwfp-groups.csv",
  "./downloads/sample-products.csv",
  "./downloads/sample-resource-sites.geojson",
  "./downloads/sample-plan-summary.md"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    ))
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request))
  );
});
