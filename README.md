# Directorio de oficios (PWA)

Plataforma tipo "Didi para oficios" que conecta clientes con profesionales de
oficios en México, con **verificación humana real** (llamada + referencia).
Web con enfoque SEO, instalable como PWA.

> El contexto completo del producto, el modelo de negocio y el sistema de
> diseño están en [`CLAUDE.md`](./CLAUDE.md).

## Stack

- **Flask + Jinja2** (renderizado en servidor, necesario para el SEO)
- **htmx** para acciones sin recarga (aprobar altas, etc.)
- **PostgreSQL** vía SQLAlchemy (cae a SQLite en local si no hay `DATABASE_URL`)
- **PWA**: `manifest.json` + service worker en JS plano
- Despliegue en **Railway**

## Estructura

```
app/
├── __init__.py              # application factory (create_app)
├── config.py                # configuración por variables de entorno
├── extensions.py            # instancias db / migrate
├── models.py                # modelos SQLAlchemy (las 5 tablas + catálogos)
├── cli.py                   # comando `flask seed`
├── blueprints/
│   ├── public/              # landing SEO, directorio, perfil, solicitud
│   ├── profesionales/       # alta del profesional
│   └── admin/               # cola de verificación (aprobar/rechazar)
├── templates/               # Jinja2 (base + páginas por blueprint)
└── static/
    ├── css/estilo.css       # sistema de diseño (plano técnico / cinta métrica)
    ├── js/htmx.min.js
    ├── manifest.json
    └── sw.js                # service worker (incluye esqueleto de push)
wsgi.py                      # punto de entrada (gunicorn / flask run)
Procfile, railway.json       # despliegue en Railway
```

## Correr en local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # ajusta SECRET_KEY (y DATABASE_URL si usas Postgres)

export FLASK_APP=wsgi
flask seed                    # crea tablas + siembra oficios, zonas y un demo
flask run --debug
```

Abre <http://localhost:5000>. Rutas clave:

| Ruta                              | Descripción                              |
|-----------------------------------|------------------------------------------|
| `/`                               | Portada                                  |
| `/directorio`                     | Directorio filtrable por oficio y zona   |
| `/oficio/<oficio>/<zona>`         | Landing SEO (ej. `/oficio/plomero/coyoacan`) |
| `/profesional/<id>`               | Perfil del profesional                   |
| `/solicitar`                      | Formulario de solicitud del cliente      |
| `/profesionales/alta`             | Registro del profesional                 |
| `/profesionales/<token>/leads`    | Bandeja de leads (acceso por enlace mágico) |
| `/profesionales/<token>/creditos` | Compra de créditos (paquetes escalonados)|
| `/admin/`                         | Cola de verificación + alta directa + enlaces |
| `/admin/alta-directa`             | Alta directa de un profesional de la red |
| `/salud`                          | Health check para Railway                |

El `flask seed` imprime el enlace de leads del profesional demo para probar
el flujo. El panel de admin también lista los enlaces de cada profesional
aprobado.

## Base de datos y migraciones

La carpeta `migrations/` está versionada, con la migración inicial ya generada.

- **Local rápido:** `flask seed` usa `db.create_all()` y siembra catálogos +
  datos de demo (SQLite, sin configurar nada).
- **Producción / esquema real:** `flask db upgrade` aplica las migraciones. El
  `Procfile` lo corre solo en el paso `release` de cada despliegue.
- Cuando cambie el modelo: `flask db migrate -m "descripción"` genera la nueva
  migración; revísala y commitéala.

## Despliegue en Railway

1. Crea un proyecto en Railway y agrega el plugin **PostgreSQL** (inyecta
   `DATABASE_URL` automáticamente).
2. Conecta este repositorio; Railway detecta Python (Nixpacks) e instala
   `requirements.txt`.
3. Define las variables de entorno en el servicio (ver `.env.example`):
   - **Obligatoria:** `SECRET_KEY` (cadena larga y aleatoria).
   - **Recomendada:** `CLOUDINARY_URL` — sin ella, las fotos de perfil se
     guardan en disco local, que en Railway es **efímero** (se pierden al
     redeploy). Para que las fotos persistan, configúrala.
   - **Opcionales (activan cada módulo):** `VAPID_*` (push), `TWILIO_*` (SMS,
     pendiente), `STRIPE_*` (pagos, pendiente).
4. El `release` corre `flask db upgrade` (crea el esquema en Postgres).
5. Tras el primer deploy, siembra los catálogos de oficios/zonas una vez:
   `flask seed` desde la consola de Railway (o cárgalos por el panel de admin).

El endpoint `/salud` sirve como health check.

### Modo demo

Para mostrarlo a un cliente de punta a punta antes de conectar Twilio, define
`DEMO_MODE=1`. Con esto, una solicitud creada en vivo se marca como verificada
al instante (salta el SMS) y aparece de inmediato en la bandeja del profesional
que coincide; los pagos siguen simulados. Se muestra una cinta "Modo
demostración" en todas las páginas. **Déjalo apagado en producción real.**

## Estado actual

Construido: esqueleto Flask, modelos de datos, directorio + landing SEO +
perfil, formulario de solicitud, alta de profesional, panel de verificación
con htmx, sistema de diseño y PWA base.

También construido: **flujo de leads y créditos** — bandeja del profesional
(acceso por enlace mágico, sin login), desbloqueo de contacto que descuenta un
crédito de forma atómica e idempotente (registra `desbloqueos` y
`movimientos_credito`), y compra de créditos por paquetes escalonados.

Y **notificaciones Web Push** — el profesional activa las notificaciones desde
su bandeja (VAPID + service worker); cuando llega un lead válido que coincide
con su oficio y zona se le envía un push con `pywebpush`. Genera las llaves con:

```bash
flask vapid-keys      # copia la salida al .env
```

Si no hay llaves VAPID configuradas, el push se omite en silencio (la app
sigue funcionando en local sin configurarlo).

Y **carga de foto de perfil** del profesional — en el alta pública y en el alta
directa del admin. Usa Cloudinary cuando hay `CLOUDINARY_URL`; si no, guarda en
`static/uploads/` (fallback local para trabajar sin cuenta). La foto se muestra
en el directorio y el perfil; si no hay, se usa un avatar con la inicial.

Pendiente de conectar (marcado con `TODO` en el código):

- Verificación del teléfono del cliente por SMS (Twilio Verify) — hoy la
  bandeja solo muestra solicitudes ya marcadas como verificadas, y el push se
  dispara cuando `telefono_verificado` pasa a True (ese punto lo activará
  Twilio).
- Respaldo de notificación (SMS/correo) para iOS < 16.4 o sin PWA instalada.
- Pasarela de pago real (Stripe / Conekta): la compra de créditos está
  simulada; falta crear la sesión de pago y acreditar vía webhook.
- Portafolio de fotos de trabajos hechos (fuera de alcance por ahora; buen
  candidato a agregar pronto).
- Envío automático del enlace de leads al profesional al aprobarlo
  (hoy se copia desde el panel de admin).
