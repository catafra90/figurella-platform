// app/static/js/service-worker.js

const CACHE_NAME = 'figurella-cache-v18';
const OFFLINE_URL = '/offline';

// Everything we want pre-cached on install:
const urlsToPreCache = [
  '/',
  '/clients',
  '/daily-report/',         // combined wizard route
  '/static/js/combined.js',
  '/static/css/tailwind.min.css',
  '/static/js/sw-init.js',
  '/static/js/queue.js',
  '/static/images/figurella-logo.png',
  '/static/manifest.json',
  '/offline'
];

// INSTALL: cache our core assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache =>
        Promise.all(
          urlsToPreCache.map(async url => {
            try {
              const response = await fetch(url, { cache: 'no-store' });
              if (response.ok) {
                await cache.put(url, response.clone());
                console.log('✅ Cached', url);
              } else {
                console.warn('⚠️ Failed to cache', url, response.status);
              }
            } catch (err) {
              console.warn('⚠️ Error fetching', url, err);
            }
          })
        )
      )
  );
  self.skipWaiting();
});

// ACTIVATE: clear old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            console.log('🧹 Deleting old cache', key);
            return caches.delete(key);
          }
        })
      )
    )
  );
  self.clients.claim();
});

// FETCH: handle navigation to wizard, then cache-first, then network, then offline fallback
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  // Special handling for wizard navigation
  if (event.request.mode === 'navigate' && event.request.url.includes('/daily-report/')) {
    event.respondWith(
      caches.match('/daily-report/').then(cachedResponse => cachedResponse || fetch(event.request))
    );
    return;
  }

  // Default cache-first strategy
  event.respondWith(
    caches.match(event.request, { ignoreSearch: true }).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request)
        .then(networkResponse => {
          if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return networkResponse;
        })
        .catch(() => caches.match(OFFLINE_URL));
    })
  );
});
