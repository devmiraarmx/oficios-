/* Service worker mínimo de la PWA.
   Estrategia: caché del "app shell" para carga rápida; la red manda para
   contenido dinámico. Las notificaciones push (Web Push API) se conectan
   cuando exista el backend con pywebpush + VAPID.
*/
const CACHE = "oficios-v1";
const APP_SHELL = [
  "/",
  "/static/css/estilo.css",
  "/static/manifest.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((claves) =>
      Promise.all(claves.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;                 // no cachear POST
  event.respondWith(
    fetch(req).catch(() => caches.match(req).then((r) => r || caches.match("/")))
  );
});

/* --- Notificaciones push (esqueleto; se activa con el backend VAPID) --- */
self.addEventListener("push", (event) => {
  const datos = event.data ? event.data.json() : {};
  const titulo = datos.titulo || "Nueva solicitud";
  event.waitUntil(
    self.registration.showNotification(titulo, {
      body: datos.cuerpo || "Tienes una nueva solicitud que coincide con tu oficio.",
      icon: "/static/img/icono-192.png",
      data: datos.url || "/"
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(clients.openWindow(event.notification.data || "/"));
});
