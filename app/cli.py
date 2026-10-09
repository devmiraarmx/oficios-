"""Comandos de consola para desarrollo.

    flask --app wsgi seed        # crea tablas y siembra catálogos + demo

Útil para levantar el proyecto local sin configurar Postgres (cae a SQLite).
"""
import click
from flask import Flask

from app.extensions import db
from app.models import (
    Oficio,
    Zona,
    Profesional,
    Resena,
    Solicitud,
    Urgencia,
    EstadoProfesional,
    CategoriaOficio,
)

# (nombre, slug, sección) — ver SECCIONES_OFICIO en app/models.py
OFICIOS = [
    # Obra negra y estructura
    ("Albañil", "albanil", "obra_negra"),
    ("Bloquero", "bloquero", "obra_negra"),
    ("Fierrero", "fierrero", "obra_negra"),
    ("Cimbrador", "cimbrador", "obra_negra"),
    ("Colador", "colador", "obra_negra"),
    # Acabados
    ("Yesero", "yesero", "acabados"),
    ("Pastero", "pastero", "acabados"),
    ("Estuquero", "estuquero", "acabados"),
    ("Tablaroquero", "tablaroquero", "acabados"),
    ("Colocador de Pisos y Azulejos", "colocador-pisos-azulejos", "acabados"),
    ("Pintor", "pintor", "acabados"),
    # Instalaciones
    ("Plomero", "plomero", "instalaciones"),
    ("Electricista", "electricista", "instalaciones"),
    ("Instalador de Sistemas contra Incendios", "sistemas-contra-incendios", "instalaciones"),
    # Carpintería, herrería y cerrajería
    ("Carpintero", "carpintero", "carpinteria_herreria"),
    ("Carpintero de Obra", "carpintero-de-obra", "carpinteria_herreria"),
    ("Herrero", "herrero", "carpinteria_herreria"),
    ("Cerrajero", "cerrajero", "carpinteria_herreria"),
]

ESPECIALISTAS = [
    ("Arquitecto", "arquitecto"),
    ("Ingeniero Civil", "ingeniero-civil"),
    ("Ingeniero Eléctrico", "ingeniero-electrico"),
    ("Topógrafo", "topografo"),
    ("Diseñador de Interiores", "disenador-interiores"),
    ("Perito / DRO", "perito-dro"),
]

ZONAS = [
    ("Coyoacán", "coyoacan", "Ciudad de México"),
    ("Benito Juárez", "benito-juarez", "Ciudad de México"),
    ("Álvaro Obregón", "alvaro-obregon", "Ciudad de México"),
    ("Centro", "cancun-centro", "Cancún"),
    ("Zona Hotelera", "cancun-zona-hotelera", "Cancún"),
]


def registrar_comandos(app: Flask) -> None:
    @app.cli.command("seed")
    def seed():
        """Crea las tablas y siembra catálogos y un profesional de demostración."""
        db.create_all()

        for nombre, slug, seccion in OFICIOS:
            if not Oficio.query.filter_by(slug=slug).first():
                db.session.add(Oficio(
                    nombre=nombre, slug=slug, seccion=seccion,
                    categoria=CategoriaOficio.OFICIO.value,
                ))

        for nombre, slug in ESPECIALISTAS:
            if not Oficio.query.filter_by(slug=slug).first():
                db.session.add(Oficio(
                    nombre=nombre, slug=slug,
                    categoria=CategoriaOficio.ESPECIALISTA.value,
                ))

        for nombre, slug, ciudad in ZONAS:
            if not Zona.query.filter_by(slug=slug).first():
                db.session.add(Zona(nombre=nombre, slug=slug, ciudad=ciudad))

        db.session.commit()

        if not Profesional.query.first():
            plomero = Oficio.query.filter_by(slug="plomero").first()
            coyoacan = Zona.query.filter_by(slug="coyoacan").first()
            demo = Profesional(
                nombre="Juan Ramírez",
                telefono="+525500000000",
                zona="Coyoacán",
                anios_experiencia=12,
                descripcion="Plomería general, fugas, calentadores y drenaje.",
                telefono_referencia="+525511111111",
                estado=EstadoProfesional.APROBADO,
                saldo_creditos=5,
            )
            demo.oficios.append(plomero)
            demo.zonas.append(coyoacan)
            db.session.add(demo)
            db.session.flush()
            db.session.add(Resena(profesional_id=demo.id, calificacion=5,
                                  comentario="Puntual y resolvió la fuga rápido."))
            db.session.add(Resena(profesional_id=demo.id, calificacion=4,
                                  comentario="Buen trabajo, precio justo."))
            db.session.commit()

            click.echo(f"  Enlace de leads del demo: /profesionales/{demo.token_acceso}/leads")

        # Solicitudes verificadas de demostración (leads válidos para el demo).
        if not Solicitud.query.first():
            db.session.add(Solicitud(
                oficio="Plomero", zona="Coyoacán",
                descripcion="Fuga en el calentador de agua, urge revisión.",
                urgencia=Urgencia.HOY, nombre_cliente="María López",
                telefono_cliente="5512345678", telefono_verificado=True,
            ))
            db.session.add(Solicitud(
                oficio="Plomero", zona="Coyoacán",
                descripcion="Cambio de llaves y sellado en el baño.",
                urgencia=Urgencia.ESTA_SEMANA, nombre_cliente="Jorge Díaz",
                telefono_cliente="5598765432", telefono_verificado=True,
            ))
            db.session.commit()

        click.echo("Seed completado: catálogos, demo y solicitudes listos.")

    @app.cli.command("vapid-keys")
    def vapid_keys():
        """Genera un par de llaves VAPID para Web Push. Copia la salida al .env."""
        from app.notificaciones import generar_llaves_vapid

        pub, priv = generar_llaves_vapid()
        click.echo("VAPID_PUBLIC_KEY=" + pub)
        click.echo("VAPID_PRIVATE_KEY=" + priv)
        click.echo("VAPID_CLAIM_EMAIL=mailto:contacto@ejemplo.mx")
