# Proyecto: directorio de oficios (PWA) — [nombre pendiente]

Plataforma tipo "Didi para oficios" que conecta clientes con profesionales de
oficios (plomeros, electricistas, albañiles, etc.) en México. Web con enfoque
SEO, instalable como PWA. Arranque en Ciudad de México y Cancún.

Diferenciador principal: **verificación humana real** (llamada telefónica +
referencia) en vez de verificación automatizada por identificación, sobre un
directorio curado, no un directorio abierto. Este es el elemento de marca que
más ha resonado en la fase de diseño — cualquier copy o UI nueva debería
reforzarlo, no diluirlo con lenguaje corporativo genérico ("verificado" a
secas, insignias azules sin explicación, etc.).

Competidores de referencia: Mandy y Fixman (México), Cronoshare (modelo de
pago por lead, con operación en México), TaskRabbit y Thumbtack (patrones de
UX de reserva y cotización).

## Contexto del desarrollador

Un solo desarrollador (founder técnico) construye el MVP en un plazo
aproximado de 1 mes, con experiencia previa en Flask, Python, dashboards y
despliegue en Railway. Priorizar herramientas y patrones que no requieran
curva de aprendizaje nueva — evitar frameworks frontend pesados (React/Next.js)
salvo que se pida explícitamente.

## Modelo de negocio

- **MVP: pago por lead.** El profesional compra créditos prepago; cada vez
  que desbloquea el contacto de una solicitud se descuenta un crédito. El
  cliente nunca paga. Se eligió este modelo (en vez de comisión por servicio)
  para evitar procesar pagos de servicio dentro de la app.
- Paquetes de créditos con precio decreciente por volumen (ej. 5 / 10 "más
  popular" / 20 créditos), vendidos vía Stripe o Conekta.
- **Fase 2 (después de ~3 meses), aún no construir:** suscripción premium
  freemium (posición destacada, insignia, leads ilimitados o con descuento,
  estadísticas de perfil); del lado del cliente, solicitud prioritaria de
  pago (envío simultáneo a varios profesionales) y garantía del servicio de
  pago opcional.
- Financiamiento cerrado entre 3 socios (un inversionista, un experto en el
  sector de oficios, y el desarrollador), sin inversión externa por ahora.
  La valoración de la aportación del desarrollador (sweat equity vs. pago
  reducido + equity) está pendiente de definir con los socios.

## Alcance del MVP

Construir:

- Landing pages SEO por combinación oficio × ciudad (ej. "plomero en
  Coyoacán"), renderizadas del lado del servidor para ser indexables.
- Directorio de profesionales, filtrable por oficio y zona.
- Perfil de profesional: foto, oficio(s), zona de cobertura, años de
  experiencia, descripción corta, calificación con estrellas, reseñas.
- Formulario de solicitud de servicio (cliente): descripción breve,
  urgencia, nombre, teléfono. Sin registro ni contraseña — cero fricción.
- El número de contacto del profesional permanece oculto hasta que paga por
  el lead (modelo tipo Cronoshare), no se muestra libre en el directorio.
- Verificación de teléfono del cliente vía SMS (Twilio Verify) antes de que
  la solicitud cuente como lead válido, para filtrar leads de baja calidad.
- Registro/alta del profesional: foto, nombre, teléfono, oficio(s), zona,
  años de experiencia, descripción, y el teléfono de una referencia. **No se
  pide identificación oficial (INE)** — se descartó por fricción y por las
  obligaciones más pesadas de la LFPDPPP al manejar identificaciones.
- Verificación manual del profesional: llamada de verificación + checar la
  referencia. No hay verificación automatizada en el MVP.
- Panel de administración simple: cola de altas de profesional pendientes,
  con botones de aprobar/rechazar. Sin roles ni permisos — es solo para el
  founder y su socio.
- Bandeja de leads del profesional, con notificación push (Web Push API)
  cuando llega una solicitud que coincide con su oficio y zona. En iOS el
  push solo funciona desde 16.4+; considerar un respaldo (SMS o correo).
- Compra de créditos vía pasarela de pago (paquetes escalonados).
- Contacto entre cliente y profesional por WhatsApp o llamada directa, fuera
  de la app — no hay chat propio dentro de la plataforma.
- Aviso de privacidad accesible desde el formulario de solicitud (obligación
  LFPDPPP al recabar nombre y teléfono).

Explícitamente fuera de alcance por ahora (no construir sin confirmarlo):

- Botón de "reportar" un perfil.
- Toggle de disponible / no disponible del profesional.
- Login o autenticación del profesional.
- Portafolio de fotos de trabajos anteriores (buen candidato a agregar
  pronto — alto valor de confianza, bajo costo de construcción).
- Comisión por servicio, suscripción, freemium, publicidad.
- Solicitud prioritaria y garantía de servicio pagadas.

## Modelo de datos (tablas principales)

- **profesionales** — id, nombre, telefono, zona, anios_experiencia, estado
  (pendiente / aprobado / rechazado), saldo_creditos, foto_url, descripcion,
  telefono_referencia.
- **solicitudes** — id, oficio, zona, descripcion, telefono_cliente,
  telefono_verificado (bool), creado_en.
- **desbloqueos** — id, profesional_id (FK), solicitud_id (FK), creado_en.
  Registra cada compra de lead; es la tabla que mide el negocio.
- **movimientos_credito** — id, profesional_id (FK), tipo (compra/consumo),
  cantidad, creado_en. Historial completo del saldo, para auditoría.
- **resenas** — id, profesional_id (FK), calificacion, comentario.

## Stack técnico

- **Backend y páginas:** Flask + Jinja2, renderizado en servidor (necesario
  para el SEO — nada de SPA client-side para las páginas públicas).
- **Interactividad:** htmx para acciones sin recarga (desbloquear un lead,
  acciones del panel de admin) — evita necesitar un framework frontend.
- **Base de datos:** PostgreSQL vía SQLAlchemy.
- **Hosting:** Railway.
- **Pagos (créditos):** Stripe o Conekta (Conekta si se quiere aceptar pago
  en OXXO, común en el mercado mexicano).
- **Verificación de teléfono:** Twilio Verify (~$1 MXN por verificación
  exitosa en México; factura en USD sin CFDI, revisar con contador).
- **Fotos de perfil:** Cloudinary (plan gratuito cubre el volumen inicial).
- **PWA:** manifest.json + service worker en JavaScript plano;
  notificaciones push con `pywebpush` del lado de Flask.

## Sistema de diseño

Dirección visual confirmada y bien recibida — mantenerla en cualquier UI
nueva, no reemplazarla por un look genérico de SaaS:

- **Motivo:** plano técnico / cinta métrica — línea de cotas punteada,
  tarjetas tipo "ficha técnica", datos mostrados como si fueran medidas.
  Elemento de marca central: un sello circular rotado de "verificado a
  mano", que traduce la verificación humana en un elemento gráfico.
- **Paleta:** papel `#F7F5F0`, tinta `#1B2430`, acento naranja de seguridad
  `#E8622C` (hover `#C74E1F`), acero `#3C5A73`, musgo/verificado `#3F6B4A`,
  bordes `#D8D3C7`. Deliberadamente fuera de los clichés de diseño con IA
  (nada de beige + acento terracota, ni fondo negro con neón).
- **Tipografía:** Space Grotesk (titulares), Inter (cuerpo), IBM Plex Mono
  (datos y métricas — años de experiencia, calificaciones, precios).
- **Naming:** aún sin definir con los socios. Al elegir nombre, validar que
  no colisione con resultados de búsqueda no relacionados (el competidor
  Mandy comparte nombre con una película de 2018 y pierde casi todo su
  tráfico de marca por eso).

## Próximos pasos técnicos

- Traducir el modelo de datos a modelos de SQLAlchemy.
- Armar el esqueleto de carpetas del proyecto Flask.
- Configurar despliegue en Railway.
