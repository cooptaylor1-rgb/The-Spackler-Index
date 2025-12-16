// Service Worker for The Spackler Index PWA
// Dynamic cache versioning for reliable iOS home-screen updates

// Cache version - updated on each deploy via version check
// The actual invalidation happens when the SW file changes (byte-different)
const CACHE_VERSION = 'v3';
const CACHE_NAME = `spackler-${CACHE_VERSION}`;

const urlsToCache = [
  '/',
  '/static/index.html',
  '/static/offline.html',
  '/manifest.json',
  '/static/manifest.json',
  '/static/images/apple-touch-icon.png',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png',
  '/static/images/gopher.jpg',
  '/static/images/spackler-logo.jpg'
];

// Install service worker and cache assets
self.addEventListener('install', event => {
  console.log('[SW] Installing new version:', CACHE_NAME);
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('[SW] Skip waiting - taking over immediately');
        return self.skipWaiting();
      })
  );
});

// Activate and clean up old caches
self.addEventListener('activate', event => {
  console.log('[SW] Activating new version:', CACHE_NAME);
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName.startsWith('spackler-')) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Claiming all clients');
      return self.clients.claim();
    })
  );
});

// Fetch strategy: network-first for navigation and HTML, cache-first for static assets
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const requestUrl = new URL(event.request.url);

  // Skip API calls - always go to network
  if (requestUrl.pathname.startsWith('/api/')) {
    return;
  }

  // Network-first for navigation (HTML pages)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache the fresh response
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        })
        .catch(() => {
          // Offline fallback
          return caches.match(event.request)
            .then(cached => cached || caches.match('/static/offline.html'));
        })
    );
    return;
  }

  // For other assets: stale-while-revalidate pattern
  // Return cached immediately, but fetch fresh in background
  event.respondWith(
    caches.match(event.request).then(cached => {
      const fetchPromise = fetch(event.request)
        .then(response => {
          // Update cache with fresh response
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          return response;
        })
        .catch(() => null);

      // Return cached immediately if available, otherwise wait for fetch
      return cached || fetchPromise || caches.match('/static/offline.html');
    })
  );
});

// Listen for messages from the client
self.addEventListener('message', event => {
  if (event.data === 'skipWaiting') {
    console.log('[SW] Received skipWaiting message');
    self.skipWaiting();
  }
});