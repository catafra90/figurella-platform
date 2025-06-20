// app/static/js/service-worker.js

const CACHE_NAME = 'figurella-cache-v18';
const OFFLINE_URL = '/offline';

// Everything we want pre-cached on install:
const urlsToPreCache = [
  '/',
  '/clients',
  '/step1/',
  '/step2/',
  '/step3/',
  '/step4/',
  '/step5/',
  '/offline',

  '/static/css/tailwind.min.css',
  '/static/js/sw-init.js',
  '/static/js/queue.js',
  '/static/images/figurella-logo.png',
  '/static/manifest.json'
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

// ACTIVATE: clear out any old caches
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

// FETCH: serve from cache, then network, then offline fallback
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request, { ignoreSearch: true }).then(cachedResponse => {
      if (cachedResponse) {
        return cachedResponse;
      }

      return fetch(event.request)
        .then(networkResponse => {
          // Put a copy in the cache for next time
          if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return networkResponse;
        })
        .catch(() => {
          // If both cache & network fail, show offline page
          return caches.match(OFFLINE_URL);
        });
    })
  );
});
