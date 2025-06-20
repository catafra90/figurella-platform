const CACHE_NAME = "figurella-cache-v16";
const OFFLINE_URL = "/offline";

const urlsToPreCache = [
  "/", "/clients", "/step1/", "/step2/", "/step3/", "/step4/", "/step5/", "/offline",
  "/static/js/queue.js",
  "/static/images/figurella-logo.png",
  "/static/css/tailwind.min.css",
  "/static/manifest.json"
];

// ✅ INSTALL: Cache everything in urlsToPreCache
self.addEventListener("install", event => {
  console.log("✅ Installing service worker...");
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      Promise.all(
        urlsToPreCache.map(async url => {
          try {
            const response = await fetch(url, { cache: "no-store" });
            if (response.ok) {
              await cache.put(url, response.clone());
              console.log("✅ Cached:", url);
            } else {
              console.warn("⚠️ Failed to cache:", url, response.status);
            }
          } catch (err) {
            console.warn("⚠️ Error fetching:", url, err);
          }
        })
      )
    )
  );
  self.skipWaiting();
});

// ✅ ACTIVATE: Delete old cache
self.addEventListener("activate", event => {
  console.log("♻️ Activating service worker...");
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            console.log("🧹 Removing old cache:", key);
            return caches.delete(key);
          }
        })
      )
    )
  );
  self.clients.claim();
});

// ✅ FETCH: Serve from cache if available
self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request, { ignoreSearch: true }).then(cached => {
      if (cached) return cached;
      return fetch(event.request)
        .then(response => {
          if (response && response.status === 200 && response.type === "basic") {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(OFFLINE_URL));
    })
  );
});
