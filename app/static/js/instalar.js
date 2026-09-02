/* Banner de instalación de la PWA.
   - Android (Chrome/Edge) y Desktop: captura `beforeinstallprompt` y el botón
     "Instalar" dispara el instalador nativo del sistema.
   - iPhone (Safari): iOS no permite instalar por botón; se muestran las
     instrucciones (Compartir → Agregar a inicio).
   Se oculta si la app ya está instalada o si el usuario lo cerró.
   El descarte usa sessionStorage: al cerrar con la ✕ no vuelve a salir
   durante esa sesión, pero reaparece en la siguiente visita.
*/
(function () {
  const banner = document.getElementById("instalar-banner");
  if (!banner) return;

  const btn = document.getElementById("instalar-btn");
  const cerrar = document.getElementById("instalar-cerrar");
  const sub = document.getElementById("instalar-banner__sub");

  const yaInstalada =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  // sessionStorage: el descarte dura solo la sesión actual; en la próxima
  // visita (nueva sesión) el banner vuelve a ofrecerse.
  function descartado() {
    try { return sessionStorage.getItem("instalar-descartado") === "1"; }
    catch (e) { return false; }
  }
  function marcarDescartado() {
    try { sessionStorage.setItem("instalar-descartado", "1"); } catch (e) {}
  }

  if (yaInstalada || descartado()) return;

  const mostrar = () => { banner.hidden = false; };
  const ocultar = () => { banner.hidden = true; };

  cerrar && cerrar.addEventListener("click", () => { marcarDescartado(); ocultar(); });

  // --- Android / Desktop (Chromium): instalación nativa por botón ---
  let promptDiferido = null;

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();          // evitamos el mini-infobar por defecto
    promptDiferido = e;
    mostrar();
  });

  btn && btn.addEventListener("click", async () => {
    if (!promptDiferido) return;
    promptDiferido.prompt();
    try {
      const { outcome } = await promptDiferido.userChoice;
      if (outcome === "accepted") marcarDescartado();
    } catch (e) {}
    promptDiferido = null;
    ocultar();
  });

  window.addEventListener("appinstalled", () => { marcarDescartado(); ocultar(); });

  // --- iPhone (Safari): sin prompt nativo, mostramos instrucciones ---
  const ua = window.navigator.userAgent;
  const esIOS = /iphone|ipad|ipod/i.test(ua);
  const esSafariReal = /safari/i.test(ua) && !/crios|fxios|edgios|opios/i.test(ua);

  if (esIOS && esSafariReal) {
    if (btn) btn.hidden = true; // en iOS no puede disparar la instalación
    if (sub) sub.textContent = 'Toca Compartir y luego “Agregar a inicio”.';
    mostrar();
  }
})();
