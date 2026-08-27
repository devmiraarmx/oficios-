"""Application factory.

Crea y configura la app Flask, inicializa extensiones y registra los
blueprints. Se usa como `create_app()` desde gunicorn/wsgi.
"""
from flask import Flask

from app.config import Config
from app.extensions import db, migrate


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensiones
    db.init_app(app)
    migrate.init_app(app, db)

    # Modelos (import necesario para que Flask-Migrate los descubra)
    from app import models  # noqa: F401

    # Blueprints
    from app.blueprints.public import bp as public_bp
    from app.blueprints.profesionales import bp as profesionales_bp
    from app.blueprints.admin import bp as admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(profesionales_bp, url_prefix="/profesionales")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Comandos de consola (seed de catálogos de demo)
    from app.cli import registrar_comandos
    registrar_comandos(app)

    # Filtro de plantilla: teléfono -> enlace de WhatsApp (wa.me).
    # El contacto cliente<->profesional ocurre por WhatsApp/llamada, fuera de
    # la app; no hay chat propio.
    @app.template_filter("whatsapp")
    def _whatsapp(telefono):
        digitos = "".join(c for c in (telefono or "") if c.isdigit())
        if len(digitos) == 10:  # número nacional MX sin lada de país
            digitos = "52" + digitos
        return "https://wa.me/" + digitos

    # Chequeo de salud para Railway
    @app.route("/salud")
    def salud():
        return {"estado": "ok"}, 200

    return app
