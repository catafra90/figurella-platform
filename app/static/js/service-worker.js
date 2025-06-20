const CACHE_NAME = "figurella-cache-v1";
const OFFLINE_URL = "/offline";

const ASSETS = [
  "/", "/step1/", "/step2/", "/step3/", "/step4/", "/step5/",
  "/static/css/tailwind.min.css",
  "/static/js/queue.js",
  "/static/js/sw-init.js",
  "/static/images/figurella-logo.png",
  "/static/manifest.json",
  OFFLINE_URL
];

self.addEventListener("install", evt => {
  evt.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", evt => {
  evt.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", evt => {
  // Only handle GETs
  if (evt.request.method !== "GET") return;

  // HTML pages: try network first, fallback to cache, then offline page
  if (evt.request.mode === "navigate") {
    evt.respondWith(
      fetch(evt.request)
        .then(res => {
          // update cache in background
          const copy = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(evt.request, copy));
          return res;
        })
        .catch(() =>
          caches.match(evt.request).then(cached => cached || caches.match(OFFLINE_URL))
        )
    );
    return;
  }

  // Other requests (CSS/JS/images): cache-first, then network
  evt.respondWith(
    caches.match(evt.request).then(cached => {
      return cached || fetch(evt.request).then(res => {
        if (res && res.status === 200 && res.type === "basic") {
          const copy = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(evt.request, copy));
        }
        return res;
      });
    }).catch(() => {
      // if both fail, and it’s an image, you could return a fallback image here
      return null;
    })
  );
});
