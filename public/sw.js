// Service worker: cache do "casco" do app para abrir rápido e funcionar como app instalado.
const CACHE = 'rumo-v2';
const SHELL = ['/', '/index.html', '/css/app.css', '/js/app.js', '/js/util.js', '/icon.svg', '/icon-192.png', '/manifest.json'];
self.addEventListener('install', (e) => { e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.pathname.startsWith('/api/')) return;
  // network-first, fallback to cache (so updates arrive immediately when online)
  e.respondWith(
    fetch(e.request).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match(e.request).then((r) => r || caches.match('/index.html')))
  );
});

// Lembretes: mostra a notificação enviada pelo servidor.
self.addEventListener('push', (e) => {
  let data = {};
  try { data = e.data ? e.data.json() : {}; } catch { data = { body: e.data && e.data.text() }; }
  e.waitUntil(self.registration.showNotification(data.title || 'Rumo', {
    body: data.body || 'Seu dia está te esperando.',
    icon: '/icon-192.png',
    badge: '/icon-192.png',
    data: { url: data.url || '/#/hoje' },
    tag: 'rumo-diario',
  }));
});

// Ao tocar na notificação, abre (ou foca) o app na tela Hoje.
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const url = e.notification.data?.url || '/#/hoje';
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
    for (const c of list) { if ('focus' in c) { c.navigate(url).catch(() => {}); return c.focus(); } }
    return self.clients.openWindow(url);
  }));
});
