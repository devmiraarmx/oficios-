/* Suscripción a notificaciones Web Push desde la bandeja del profesional.
   Requiere que la página exponga window.OFICIOS_PUSH = { base: "/profesionales/<token>" }.
   En iOS el push solo funciona desde 16.4+ y con la PWA instalada; si no está
   disponible, el botón se oculta y más adelante entra el respaldo (SMS/correo).
*/
(function () {
  const cfg = window.OFICIOS_PUSH;
  const boton = document.getElementById("btn-push");
  if (!cfg || !boton) return;

  const soportado =
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window;

  if (!soportado) {
    boton.style.display = "none";
    return;
  }

  function b64ToUint8(base64) {
    const pad = "=".repeat((4 - (base64.length % 4)) % 4);
    const s = (base64 + pad).replace(/-/g, "+").replace(/_/g, "/");
    const raw = atob(s);
    return Uint8Array.from([...raw].map((c) => c.charCodeAt(0)));
  }

  function estado(texto, activo) {
    boton.textContent = texto;
    boton.disabled = false;
    boton.dataset.activo = activo ? "1" : "0";
  }

  async function suscribir() {
    boton.disabled = true;
    try {
      const permiso = await Notification.requestPermission();
      if (permiso !== "granted") {
        estado("Notificaciones bloqueadas", false);
        return;
      }

      const resp = await fetch(cfg.base + "/push/clave-publica");
      const data = await resp.json();
      if (!data.habilitado) {
        boton.style.display = "none"; // servidor sin VAPID configurado
        return;
      }

      const reg = await navigator.serviceWorker.ready;
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: b64ToUint8(data.clave),
      });

      await fetch(cfg.base + "/push/suscribir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(sub),
      });
      estado("Notificaciones activadas ✓", true);
    } catch (e) {
      console.error(e);
      estado("No se pudo activar", false);
    }
  }

  // Estado inicial: ¿ya está suscrito este navegador?
  navigator.serviceWorker.ready
    .then((reg) => reg.pushManager.getSubscription())
    .then((sub) => estado(sub ? "Notificaciones activadas ✓" : "Activar notificaciones", !!sub))
    .catch(() => estado("Activar notificaciones", false));

  boton.addEventListener("click", () => {
    if (boton.dataset.activo === "1") return; // ya activadas
    suscribir();
  });
})();
