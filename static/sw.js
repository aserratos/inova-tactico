const CACHE_NAME = 'ivory-v1';
const ASSETS = [
    '/',
    '/static/manifest.json',
    'https://cdn.tailwindcss.com',
    'https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js',
    'https://cdn.jsdelivr.net/npm/chart.js',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(ASSETS);
        })
    );
});

self.addEventListener('fetch', event => {
    // Skip POST requests (they can't be cached)
    if (event.request.method !== 'GET') return;

    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request).then(fetchRes => {
                return caches.open(CACHE_NAME).then(cache => {
                    cache.put(event.request.url, fetchRes.clone());
                    return fetchRes;
                });
            });
        }).catch(() => {
            // Optional: fallback for offline images or pages
        })
    );
});
