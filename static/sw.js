const CACHE_NAME = 'raio-mods-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/static/css/base.css',
  '/static/js/base.js',
  '/static/logo.png',
  '/offline.html'
];

// Install Event: Cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// Activate Event: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
});

// Fetch Event: Network first, fall back to cache
self.addEventListener('fetch', (event) => {
  // Ignora requisições que não sejam GET ou que sejam para API/Admin
  if (event.request.method !== 'GET' || event.request.url.includes('/admin')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Se a resposta for válida, clona e atualiza o cache (estratégia Stale-While-Revalidate simples)
        if (response && response.status === 200 && response.type === 'basic') {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return response;
      })
      .catch(() => {
        // Se falhar (offline), tenta retornar do cache
        return caches.match(event.request).then((response) => {
          if (response) {
            return response;
          }
          // Se não tiver no cache e for navegação, pode retornar uma página offline (opcional)
          // return caches.match('/offline.html');
        });
      })
  );
});
