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

En local, `flask seed` usa `db.create_all()` para arrancar rápido con SQLite.
Para producción con Postgres, el flujo con Flask-Migrate es:

```bash
flask db init        # una sola vez
flask db migrate -m "esquema inicial"
flask db upgrade
```

El `Procfile` corre `flask db upgrade` en el paso `release` de cada despliegue.

## Estado actual

Construido: esqueleto Flask, modelos de datos, directorio + landing SEO +
perfil, formulario de solicitud, alta de profesional, panel de verificación
con htmx, sistema de diseño y PWA base.

También construido: **flujo de leads y créditos** — bandeja del profesional
(acceso por enlace mágico, sin login), desbloqueo de contacto que descuenta un
crédito de forma atómica e idempotente (registra `desbloqueos` y
`movimientos_credito`), y compra de créditos por paquetes escalonados.

Pendiente de conectar (marcado con `TODO` en el código):

- Verificación del teléfono del cliente por SMS (Twilio Verify) — hoy la
  bandeja solo muestra solicitudes ya marcadas como verificadas.
- Notificación push a profesionales al llegar un lead que coincide.
- Pasarela de pago real (Stripe / Conekta): la compra de créditos está
  simulada; falta crear la sesión de pago y acreditar vía webhook.
- Subida de foto de perfil a Cloudinary.
- Envío automático del enlace de leads al profesional al aprobarlo
  (hoy se copia desde el panel de admin).
