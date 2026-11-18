// Arma los enlaces de WhatsApp de la página ancla CIMANT con lo que elige el cliente.
(function () {
  // El número sale de la variable de entorno WHATSAPP_NEGOCIO (ver config.py).
  var NUMERO = (document.body.dataset.whatsapp || '').replace(/\D/g, '');
  var wa = function (txt) { return 'https://wa.me/' + NUMERO + '?text=' + encodeURIComponent(txt); };
  var estado = { urgencia: 'Programado' };
  var servicio = document.getElementById('servicio');
  var alcaldia = document.getElementById('alcaldia');
  var otroCampo = document.getElementById('servicio-otro-campo');
  var otroInput = document.getElementById('servicio-otro');
  var botones = document.querySelectorAll('.toggle button');
  var enlacesPedido = [document.getElementById('wa-pedido'), document.getElementById('wa-pie')];

  // Con "Otro", el cliente escribe el servicio a mano y eso va en el mensaje.
  function servicioElegido() {
    if (servicio.value === 'Otro') {
      return otroInput.value.trim() ? 'Otro: ' + otroInput.value.trim() : 'Otro (por definir)';
    }
    return servicio.value || 'por definir';
  }

  function actualizar() {
    otroCampo.hidden = servicio.value !== 'Otro';
    var msg = 'Hola CIMANT, quiero pedir un servicio.\n' +
      'Servicio: ' + servicioElegido() + '\n' +
      'Alcaldía: ' + (alcaldia.value || 'por definir') + '\n' +
      'Para cuándo: ' + estado.urgencia + '\n' +
      'Les envío fotos del trabajo.';
    enlacesPedido.forEach(function (a) { a.href = wa(msg); });
    botones.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.urgencia === estado.urgencia)); });
  }

  servicio.addEventListener('change', actualizar);
  alcaldia.addEventListener('change', actualizar);
  otroInput.addEventListener('input', actualizar);
  botones.forEach(function (b) {
    b.addEventListener('click', function () { estado.urgencia = b.dataset.urgencia; actualizar(); });
  });

  document.getElementById('wa-especialista').href = wa('Hola CIMANT, soy especialista y quiero registrarme en su directorio.\nOficio:\nAlcaldía donde trabajo:\nAños de experiencia:');
  document.getElementById('wa-contratista').href = wa('Hola CIMANT, soy arquitecto/contratista y quiero ofrecer mi plantilla de trabajadores.\nEmpresa o nombre:\nNúmero de trabajadores:\nOficios:');
  actualizar();
})();
