// app/static/js/service-worker.js

const CACHE_NAME = 'figurella-cache-v1';
const OFFLINE_URL = '/offline';

// List of resources to pre‐cache
const urlsToPreCache = [
  '/',
  '/daily-report/',
  '/static/css/tailwind.min.css',
  '/static/js/combined.js',
  '/static/js/sw-init.js',
  '/static/js/queue.js',
  '/static/images/figurella-logo.png',
  OFFLINE_URL
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToPreCache))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => key !== CACHE_NAME && caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.mode === 'navigate') {
    // HTML navigation requests: try network first, fallback to offline page
    event.respondWith(
      fetch(event.request).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }
  // All other requests: cache-first
  event.respondWith(
    caches.match(event.request).then(cached =>
      cached || fetch(event.request).then(resp => {
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        }
        return resp;
      })
    )
  );
});
