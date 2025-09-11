/**
 * MLBB Coach AI - Service Worker
 * Provides offline functionality, caching, and background sync
 */

const CACHE_NAME = "mlbb-coach-ai-v1.0.0";
const OFFLINE_CACHE = "mlbb-coach-offline-v1.0.0";
const RUNTIME_CACHE = "mlbb-coach-runtime-v1.0.0";

// Resources to cache on install
const PRECACHE_RESOURCES = [
  "/",
  "/static/css/main.css",
  "/static/js/main.js",
  "/manifest.json",
  "/images/icons/icon-192x192.png",
  "/images/icons/icon-512x512.png",
  "/offline.html",
  // Core app routes
  "/analyze",
  "/achievements",
  "/learning",
  "/community",
  "/dashboard",
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /^https:\/\/api\.mlbbcoach\.ai\/analytics\//,
  /^https:\/\/api\.mlbbcoach\.ai\/gamification\//,
  /^https:\/\/api\.mlbbcoach\.ai\/achievements\//,
];

// Resources that should always be fetched from network
const NETWORK_FIRST_PATTERNS = [
  /^https:\/\/api\.mlbbcoach\.ai\/analyze/,
  /^https:\/\/api\.mlbbcoach\.ai\/upload/,
  /^https:\/\/api\.mlbbcoach\.ai\/auth\//,
];

// Install event - cache core resources
self.addEventListener("install", (event) => {
  console.log("[SW] Install event");

  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => {
        console.log("[SW] Precaching resources");
        return cache.addAll(PRECACHE_RESOURCES);
      })
      .then(() => {
        console.log("[SW] Skip waiting");
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener("activate", (event) => {
  console.log("[SW] Activate event");

  event.waitUntil(
    caches
      .keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              // Delete old versions of our caches
              return (
                cacheName.startsWith("mlbb-coach-") &&
                cacheName !== CACHE_NAME &&
                cacheName !== OFFLINE_CACHE &&
                cacheName !== RUNTIME_CACHE
              );
            })
            .map((cacheName) => {
              console.log("[SW] Deleting old cache:", cacheName);
              return caches.delete(cacheName);
            })
        );
      })
      .then(() => {
        console.log("[SW] Claiming clients");
        return self.clients.claim();
      })
  );
});

// Fetch event - handle requests with caching strategies
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== "GET") {
    return;
  }

  // Skip chrome-extension requests
  if (url.protocol === "chrome-extension:") {
    return;
  }

  // Handle different types of requests
  if (url.pathname === "/") {
    // App shell - cache first
    event.respondWith(cacheFirstStrategy(request));
  } else if (url.pathname.startsWith("/static/")) {
    // Static assets - cache first with long TTL
    event.respondWith(cacheFirstStrategy(request));
  } else if (url.pathname.startsWith("/images/")) {
    // Images - cache first
    event.respondWith(cacheFirstStrategy(request));
  } else if (isApiRequest(url)) {
    // API requests - different strategies based on endpoint
    if (isNetworkFirstApi(url)) {
      event.respondWith(networkFirstStrategy(request));
    } else if (isCacheableApi(url)) {
      event.respondWith(staleWhileRevalidateStrategy(request));
    } else {
      event.respondWith(networkOnlyStrategy(request));
    }
  } else if (isAppRoute(url.pathname)) {
    // App routes - network first, fallback to app shell
    event.respondWith(appRouteStrategy(request));
  } else {
    // Other requests - network first
    event.respondWith(networkFirstStrategy(request));
  }
});

// Caching Strategies

async function cacheFirstStrategy(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log("[SW] Cache first strategy failed:", error);
    return await getOfflineFallback(request);
  }
}

async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);

    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log("[SW] Network first strategy failed, trying cache:", error);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    return await getOfflineFallback(request);
  }
}

async function staleWhileRevalidateStrategy(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  const cachedResponse = await cache.match(request);

  const fetchPromise = fetch(request)
    .then((networkResponse) => {
      if (networkResponse.ok) {
        cache.put(request, networkResponse.clone());
      }
      return networkResponse;
    })
    .catch((error) => {
      console.log("[SW] Stale while revalidate fetch failed:", error);
      return cachedResponse;
    });

  // Return cached version immediately, update in background
  return cachedResponse || fetchPromise;
}

async function networkOnlyStrategy(request) {
  try {
    return await fetch(request);
  } catch (error) {
    console.log("[SW] Network only strategy failed:", error);
    return await getOfflineFallback(request);
  }
}

async function appRouteStrategy(request) {
  try {
    return await fetch(request);
  } catch (error) {
    console.log("[SW] App route strategy failed, serving app shell:", error);
    // Serve the app shell for navigation requests
    const cache = await caches.open(CACHE_NAME);
    return await cache.match("/");
  }
}

// Helper Functions

function isApiRequest(url) {
  return (
    url.hostname === "api.mlbbcoach.ai" ||
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/analytics/") ||
    url.pathname.startsWith("/gamification/")
  );
}

function isNetworkFirstApi(url) {
  return NETWORK_FIRST_PATTERNS.some((pattern) => pattern.test(url.href));
}

function isCacheableApi(url) {
  return API_CACHE_PATTERNS.some((pattern) => pattern.test(url.href));
}

function isAppRoute(pathname) {
  const appRoutes = [
    "/analyze",
    "/achievements",
    "/learning",
    "/community",
    "/dashboard",
    "/profile",
    "/settings",
    "/leaderboards",
  ];
  return appRoutes.some((route) => pathname.startsWith(route));
}

async function getOfflineFallback(request) {
  const url = new URL(request.url);

  if (request.destination === "document") {
    // Return offline page for navigation requests
    const cache = await caches.open(CACHE_NAME);
    return await cache.match("/offline.html");
  }

  if (request.destination === "image") {
    // Return placeholder image for failed image requests
    const cache = await caches.open(CACHE_NAME);
    return await cache.match("/images/offline-placeholder.png");
  }

  // Return generic offline response
  return new Response(
    JSON.stringify({
      error: "Offline",
      message: "This feature requires an internet connection",
    }),
    {
      status: 503,
      statusText: "Service Unavailable",
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
}

// Background Sync for offline actions
self.addEventListener("sync", (event) => {
  console.log("[SW] Background sync:", event.tag);

  if (event.tag === "background-sync-analysis") {
    event.waitUntil(syncOfflineAnalyses());
  } else if (event.tag === "background-sync-achievements") {
    event.waitUntil(syncOfflineAchievements());
  } else if (event.tag === "background-sync-progress") {
    event.waitUntil(syncOfflineProgress());
  }
});

async function syncOfflineAnalyses() {
  try {
    console.log("[SW] Syncing offline analyses");

    // Get offline analyses from IndexedDB
    const offlineAnalyses = await getOfflineData("analyses");

    for (const analysis of offlineAnalyses) {
      try {
        const response = await fetch("/api/analyze", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(analysis.data),
        });

        if (response.ok) {
          // Remove from offline storage
          await removeOfflineData("analyses", analysis.id);
          console.log("[SW] Synced offline analysis:", analysis.id);
        }
      } catch (error) {
        console.log("[SW] Failed to sync analysis:", analysis.id, error);
      }
    }
  } catch (error) {
    console.log("[SW] Background sync failed:", error);
  }
}

async function syncOfflineAchievements() {
  try {
    console.log("[SW] Syncing offline achievement progress");

    const offlineProgress = await getOfflineData("achievements");

    for (const progress of offlineProgress) {
      try {
        const response = await fetch("/api/gamification/achievements/check", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(progress.data),
        });

        if (response.ok) {
          await removeOfflineData("achievements", progress.id);
          console.log("[SW] Synced offline achievement progress:", progress.id);
        }
      } catch (error) {
        console.log(
          "[SW] Failed to sync achievement progress:",
          progress.id,
          error
        );
      }
    }
  } catch (error) {
    console.log("[SW] Achievement sync failed:", error);
  }
}

async function syncOfflineProgress() {
  try {
    console.log("[SW] Syncing offline learning progress");

    const offlineProgress = await getOfflineData("learning");

    for (const progress of offlineProgress) {
      try {
        const response = await fetch("/api/gamification/learning/progress", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(progress.data),
        });

        if (response.ok) {
          await removeOfflineData("learning", progress.id);
          console.log("[SW] Synced offline learning progress:", progress.id);
        }
      } catch (error) {
        console.log(
          "[SW] Failed to sync learning progress:",
          progress.id,
          error
        );
      }
    }
  } catch (error) {
    console.log("[SW] Learning progress sync failed:", error);
  }
}

// IndexedDB helpers for offline data
async function getOfflineData(storeName) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("MLBBCoachOffline", 1);

    request.onerror = () => reject(request.error);

    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction([storeName], "readonly");
      const store = transaction.objectStore(storeName);
      const getAllRequest = store.getAll();

      getAllRequest.onsuccess = () => resolve(getAllRequest.result);
      getAllRequest.onerror = () => reject(getAllRequest.error);
    };

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains("analyses")) {
        db.createObjectStore("analyses", {
          keyPath: "id",
          autoIncrement: true,
        });
      }
      if (!db.objectStoreNames.contains("achievements")) {
        db.createObjectStore("achievements", {
          keyPath: "id",
          autoIncrement: true,
        });
      }
      if (!db.objectStoreNames.contains("learning")) {
        db.createObjectStore("learning", {
          keyPath: "id",
          autoIncrement: true,
        });
      }
    };
  });
}

async function removeOfflineData(storeName, id) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open("MLBBCoachOffline", 1);

    request.onerror = () => reject(request.error);

    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction([storeName], "readwrite");
      const store = transaction.objectStore(storeName);
      const deleteRequest = store.delete(id);

      deleteRequest.onsuccess = () => resolve();
      deleteRequest.onerror = () => reject(deleteRequest.error);
    };
  });
}

// Push notification handling
self.addEventListener("push", (event) => {
  console.log("[SW] Push event received");

  if (!event.data) {
    return;
  }

  const data = event.data.json();
  const options = {
    body: data.body,
    icon: "/images/icons/icon-192x192.png",
    badge: "/images/icons/badge-72x72.png",
    vibrate: [200, 100, 200],
    data: data.data,
    actions: data.actions || [
      {
        action: "open",
        title: "Open App",
        icon: "/images/icons/open-icon.png",
      },
      {
        action: "dismiss",
        title: "Dismiss",
        icon: "/images/icons/dismiss-icon.png",
      },
    ],
    requireInteraction: data.requireInteraction || false,
    silent: data.silent || false,
    tag: data.tag || "mlbb-coach-notification",
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});

// Notification click handling
self.addEventListener("notificationclick", (event) => {
  console.log("[SW] Notification click:", event.notification.tag, event.action);

  event.notification.close();

  if (event.action === "dismiss") {
    return;
  }

  // Handle notification click
  const urlToOpen = event.notification.data?.url || "/";

  event.waitUntil(
    clients
      .matchAll({
        type: "window",
        includeUncontrolled: true,
      })
      .then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url.includes(self.location.origin)) {
            // Focus existing window and navigate
            client.focus();
            client.navigate(urlToOpen);
            return;
          }
        }

        // Open new window
        return clients.openWindow(urlToOpen);
      })
  );
});

// Message handling for communication with main thread
self.addEventListener("message", (event) => {
  console.log("[SW] Message received:", event.data);

  if (event.data && event.data.type) {
    switch (event.data.type) {
      case "SKIP_WAITING":
        self.skipWaiting();
        break;

      case "GET_VERSION":
        event.ports[0].postMessage({
          type: "VERSION",
          version: CACHE_NAME,
        });
        break;

      case "CACHE_URLS":
        event.waitUntil(
          caches.open(RUNTIME_CACHE).then((cache) => {
            return cache.addAll(event.data.urls);
          })
        );
        break;

      case "CLEAR_CACHE":
        event.waitUntil(caches.delete(event.data.cacheName || RUNTIME_CACHE));
        break;
    }
  }
});

console.log("[SW] Service Worker loaded successfully");
