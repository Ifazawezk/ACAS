// ACAS PWA Service Worker
// Provides offline caching, background sync, and push notifications

const CACHE_NAME = 'acas-v2-fixed';
const ASSETS_TO_CACHE = [
  '/frontend/styles.css',
  '/frontend/i18n.js',
  '/frontend/manifest.json',
  '/frontend/icons/icon-192x192.png',
  '/frontend/icons/icon-512x512.png',
];

const API_CACHE = 'acas-api-v2-fixed';
const MAX_API_CACHE_TIME = 1000 * 60 * 30; // 30 minutes

// Install event - cache assets
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching assets');
        return cache.addAll(ASSETS_TO_CACHE);
      })
      .then(() => {
        console.log('[Service Worker] Installation complete');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[Service Worker] Install failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== API_CACHE) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[Service Worker] Activation complete');
        return self.clients.claim();
      })
  );
});

// Fetch event - network first, cache fallback
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // API requests - Network first
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache successful API responses
          if (response.ok) {
            const cache_control = response.headers.get('cache-control');
            if (!cache_control || !cache_control.includes('no-cache')) {
              const responseToCache = response.clone();
              caches.open(API_CACHE).then((cache) => {
                cache.put(request, responseToCache);
              });
            }
          }
          return response;
        })
        .catch(() => {
          // Return cached API response if network fails
          return caches.match(request)
            .then((cachedResponse) => {
              if (cachedResponse) {
                console.log('[Service Worker] Using cached API response:', url.pathname);
                return cachedResponse;
              }
              // Return offline page if no cache available
              return caches.match('/frontend/login.html');
            });
        })
    );
    return;
  }

  // Static assets - Cache first
  if (url.pathname.startsWith('/frontend/')) {
    event.respondWith(
      caches.match(request)
        .then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return fetch(request)
            .then((response) => {
              if (response.ok) {
                const responseToCache = response.clone();
                caches.open(CACHE_NAME).then((cache) => {
                  cache.put(request, responseToCache);
                });
              }
              return response;
            })
            .catch(() => {
              console.log('[Service Worker] Asset not available:', url.pathname);
              return caches.match('/frontend/login.html');
            });
        })
    );
    return;
  }

  // Default strategy - Network first, cache fallback
  event.respondWith(
    fetch(request)
      .catch(() => {
        return caches.match(request)
          .then((cachedResponse) => {
            return cachedResponse || caches.match('/frontend/login.html');
          });
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);
  
  if (event.tag === 'sync-comments') {
    event.waitUntil(
      // Sync pending comments when back online
      syncPendingComments()
    );
  }
});

// Push notifications
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'New notification',
    icon: '/frontend/icons/icon-192x192.png',
    badge: '/frontend/icons/icon-192x192.png',
    tag: 'acas-notification',
    requireInteraction: false,
  };

  event.waitUntil(
    self.registration.showNotification('ACAS Alert', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked');
  
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Focus existing window if available
        for (let client of clientList) {
          if (client.url === '/' || client.url.includes('static_index.html')) {
            return client.focus();
          }
        }
        // Open new window if none exists
        if (clients.openWindow) {
          return clients.openWindow('/frontend/static_index.html');
        }
      })
  );
});

// Helper function to sync pending comments
async function syncPendingComments() {
  try {
    const db = await openDatabase();
    const pendingComments = await getAllPendingComments(db);
    
    for (const comment of pendingComments) {
      try {
        const response = await fetch('/api/comments/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await getStoredToken()}`,
          },
          body: JSON.stringify(comment),
        });
        
        if (response.ok) {
          await removePendingComment(db, comment.id);
          console.log('[Service Worker] Synced comment:', comment.id);
        }
      } catch (error) {
        console.error('[Service Worker] Failed to sync comment:', error);
      }
    }
  } catch (error) {
    console.error('[Service Worker] Sync failed:', error);
  }
}

// IndexedDB helpers (stubs - implement as needed)
function openDatabase() {
  return Promise.resolve(null);
}

function getAllPendingComments(db) {
  return Promise.resolve([]);
}

function removePendingComment(db, id) {
  return Promise.resolve();
}

function getStoredToken() {
  return Promise.resolve('');
}

console.log('[Service Worker] Loaded successfully');
