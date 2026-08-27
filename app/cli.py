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
)

OFICIOS = [
    ("Plomero", "plomero"),
    ("Electricista", "electricista"),
    ("Albañil", "albanil"),
    ("Carpintero", "carpintero"),
    ("Pintor", "pintor"),
    ("Cerrajero", "cerrajero"),
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

        for nombre, slug in OFICIOS:
            if not Oficio.query.filter_by(slug=slug).first():
                db.session.add(Oficio(nombre=nombre, slug=slug))

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
