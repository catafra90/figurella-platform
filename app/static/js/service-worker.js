// app/static/js/service-worker.js

const CACHE_NAME = "figurella-cache-v18";
const OFFLINE_URL = "/offline";

const urlsToPreCache = [
  "/", "/step1/", "/step2/", "/step3/", "/step4/", "/step5/", "/clients", "/offline",
  "/static/js/queue.js",
  "/static/js/sw-init.js",
  "/static/css/tailwind.min.css",
  "/static/images/figurella-logo.png",
  "/static/manifest.json"
];

// INSTALL: cache core assets
self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToPreCache))
      .then(() => self.skipWaiting())
  );
});

// ACTIVATE: clean up old caches
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(key => key !== CACHE_NAME)
            .map(oldKey => caches.delete(oldKey))
      )
    ).then(() => self.clients.claim())
  );
});

// FETCH: 
self.addEventListener("fetch", event => {
  // 1) Only intercept top-level navigation (i.e. user clicking links / entering URLs)
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request)
        .catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  // 2) For all other GET requests (CSS, JS, images, etc.), use cache-first
  if (event.request.method === "GET") {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) {
          return cached;
        }
        return fetch(event.request).then(response => {
          // (Optional) put new fetches into cache:
          // const copy = response.clone();
          // caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          return response;
        });
      })
    );
  }
});
