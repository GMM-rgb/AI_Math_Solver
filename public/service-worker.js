const CACHE_NAME = 'math-ai-v1';
const DYNAMIC_CACHE = 'math-ai-dynamic-v1';
const MODEL_CACHE = 'math-ai-model-v1';

const urlsToCache = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-72x72.png',
  '/icons/icon-96x96.png',
  '/icons/icon-128x128.png',
  '/icons/icon-144x144.png',
  '/icons/icon-152x152.png',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
  '/model/model.json',
  '/model/weights.bin',
  '/js/tf_model.js'
];

// Install event - cache core assets
self.addEventListener('install', event => {
  event.waitUntil(
    Promise.all([
      // Cache static assets individually to log and ignore failures
      caches.open(CACHE_NAME).then(cache =>
        Promise.all(urlsToCache.map(url =>
          cache.add(new Request(url)).catch(err => {
            console.error(`Failed to cache ${url}:`, err);
          })
        ))
      ),
      // Cache model files individually
      caches.open(MODEL_CACHE).then(cache =>
        Promise.all(
          ['/model/model.json', '/model/weights.bin'].map(url =>
            cache.add(new Request(url)).catch(err => {
              console.error(`Failed to cache ${url}:`, err);
            })
          )
        )
      )
    ])
  );
});

// Fetch event - serve from cache, then network
self.addEventListener('fetch', event => {
  // Handle API requests
  if (event.request.url.includes('/chat')) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(JSON.stringify({
          response: "You're offline. Please check your connection and try again.",
          type: "error"
        }), {
          headers: { 'Content-Type': 'application/json' }
        })
      )
    );
    return;
  }
  
  // Handle other requests
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
      .catch(() => {
        if (event.request.headers.get('accept').includes('text/html')) {
          return caches.match('/offline.html');
        }
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (![CACHE_NAME, DYNAMIC_CACHE, MODEL_CACHE].includes(cacheName)) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
