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
      // Cache static assets
      caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)),
      // Cache model files separately
      caches.open(MODEL_CACHE).then(cache => 
        cache.addAll([
          '/model/model.json',
          '/model/weights.bin'
        ])
      )
    ])
  );
});

// Fetch event - serve from cache, then network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      if (response) {
        return response; // Return cached version
      }
      return fetch(event.request).then(fetchResponse => {
        // Check if we should cache this request
        if (fetchResponse.status === 200) {
          const responseToCache = fetchResponse.clone();
          
          // Cache model files in MODEL_CACHE, other dynamic responses in DYNAMIC_CACHE
          const cacheName = event.request.url.includes('/model/') ? 
            MODEL_CACHE : DYNAMIC_CACHE;
          
          caches.open(cacheName).then(cache => {
            cache.put(event.request, responseToCache);
          });
        }
        return fetchResponse;
      });
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

// Handle offline functionality
self.addEventListener('fetch', event => {
  // Handle API requests
  if (event.request.url.includes('/chat')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({
          response: "You're offline. Please check your connection and try again.",
          type: "error"
        }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
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
