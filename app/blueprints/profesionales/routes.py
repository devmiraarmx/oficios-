"""Rutas del profesional: alta/registro y (más adelante) bandeja de leads
y compra de créditos.

MVP sin login: el alta entra a la cola de verificación manual del admin.
La bandeja de leads y el desbloqueo de contacto se conectan cuando exista
el mecanismo de identificación del profesional (magic link / código).
"""
from flask import render_template, request, redirect, url_for, flash

from app.blueprints.profesionales import bp
from app.extensions import db
from app.models import Profesional, Oficio, Zona, EstadoProfesional


@bp.route("/alta", methods=["GET", "POST"])
def alta():
    if request.method == "POST":
        profesional = Profesional(
            nombre=request.form.get("nombre", "").strip(),
            telefono=request.form.get("telefono", "").strip(),
            zona=request.form.get("zona", "").strip(),
            anios_experiencia=int(request.form.get("anios_experiencia") or 0),
            descripcion=request.form.get("descripcion", "").strip(),
            telefono_referencia=request.form.get("telefono_referencia", "").strip(),
            estado=EstadoProfesional.PENDIENTE,
            saldo_creditos=0,
        )
        if not (profesional.nombre and profesional.telefono
                and profesional.telefono_referencia):
            flash("Nombre, teléfono y teléfono de referencia son obligatorios.", "error")
            return render_template(
                "profesionales/alta.html",
                oficios=Oficio.query.order_by(Oficio.nombre).all(),
                zonas=Zona.query.order_by(Zona.nombre).all(),
            )

        # Agregamos a la sesión antes de asignar relaciones para evitar que el
        # autoflush intente persistir un objeto que aún no está en la sesión.
        db.session.add(profesional)

        # Oficios y zonas seleccionados (checkboxes múltiples)
        oficio_ids = request.form.getlist("oficios")
        zona_ids = request.form.getlist("zonas")
        if oficio_ids:
            profesional.oficios = Oficio.query.filter(Oficio.id.in_(oficio_ids)).all()
        if zona_ids:
            profesional.zonas = Zona.query.filter(Zona.id.in_(zona_ids)).all()

        db.session.commit()
        # TODO: subir foto a Cloudinary; avisar al admin de un alta pendiente.
        return redirect(url_for("profesionales.alta_recibida"))

    return render_template(
        "profesionales/alta.html",
        oficios=Oficio.query.order_by(Oficio.nombre).all(),
        zonas=Zona.query.order_by(Zona.nombre).all(),
    )


@bp.route("/alta/recibida")
def alta_recibida():
    return render_template("profesionales/alta_recibida.html")
