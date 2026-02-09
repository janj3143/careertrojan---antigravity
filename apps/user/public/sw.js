/**
 * CareerTrojan Service Worker
 * Phase 2 — PWA: caching, offline support, background sync
 * 
 * Cache strategies:
 *   Static assets: cache-first (CSS, JS, images)
 *   API GET:       network-first with cache fallback
 *   API POST/PUT:  network-only
 *   Navigation:    network-first with offline fallback
 */

const CACHE_VERSION = 'careertrojan-v1';
const API_CACHE = 'careertrojan-api-v1';

const PRECACHE_URLS = [
    '/',
    '/index.html',
    '/offline.html',
    '/manifest.json',
];

// ── Install ──────────────────────────────────────────────
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_VERSION)
            .then(cache => cache.addAll(PRECACHE_URLS))
            .then(() => self.skipWaiting())
    );
});

// ── Activate — clean old caches ──────────────────────────
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(k => k !== CACHE_VERSION && k !== API_CACHE)
                    .map(k => caches.delete(k))
            )
        ).then(() => self.clients.claim())
    );
});

// ── Fetch ────────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET for caching
    if (request.method !== 'GET') return;

    // API calls — network-first
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstWithCache(request, API_CACHE));
        return;
    }

    // Navigation — network-first with offline fallback
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    const clone = response.clone();
                    caches.open(CACHE_VERSION).then(c => c.put(request, clone));
                    return response;
                })
                .catch(() => caches.match('/offline.html'))
        );
        return;
    }

    // Static assets — cache-first
    event.respondWith(cacheFirstWithNetwork(request));
});

// ── Strategies ───────────────────────────────────────────
async function networkFirstWithCache(request, cacheName) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const clone = response.clone();
            const cache = await caches.open(cacheName);
            cache.put(request, clone);
        }
        return response;
    } catch {
        const cached = await caches.match(request);
        return cached || new Response(JSON.stringify({ error: 'offline' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function cacheFirstWithNetwork(request) {
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok) {
            const clone = response.clone();
            const cache = await caches.open(CACHE_VERSION);
            cache.put(request, clone);
        }
        return response;
    } catch {
        return new Response('', { status: 408, statusText: 'Offline' });
    }
}
