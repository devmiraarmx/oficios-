"""Panel de administración simple: cola de altas pendientes con
aprobar/rechazar. Sin roles ni permisos — es solo para el founder y su socio.

Las acciones usan htmx: al aprobar/rechazar se devuelve solo la fila
actualizada, sin recargar la página.
"""
from flask import render_template, redirect, url_for, request, flash

from app.blueprints.admin import bp
from app.extensions import db
from app.models import (
    Profesional,
    Oficio,
    Zona,
    EstadoProfesional,
    OrigenProfesional,
)


@bp.route("/")
def panel():
    pendientes = (
        Profesional.query.filter_by(estado=EstadoProfesional.PENDIENTE)
        .order_by(Profesional.creado_en.asc())
        .all()
    )
    return render_template("admin/panel.html", pendientes=pendientes)


@bp.route("/alta-directa", methods=["GET", "POST"])
def alta_directa():
    """Alta directa de un profesional de la red de contactos de los socios.
    No pasa por el formulario público ni por la llamada de verificación:
    queda aprobado de inmediato y con origen = agregado_manual.
    """
    if request.method == "POST":
        profesional = Profesional(
            nombre=request.form.get("nombre", "").strip(),
            telefono=request.form.get("telefono", "").strip(),
            zona=request.form.get("zona", "").strip(),
            anios_experiencia=int(request.form.get("anios_experiencia") or 0),
            descripcion=request.form.get("descripcion", "").strip(),
            telefono_referencia=request.form.get("telefono_referencia", "").strip(),
            estado=EstadoProfesional.APROBADO,
            origen=OrigenProfesional.AGREGADO_MANUAL,
            saldo_creditos=int(request.form.get("saldo_creditos") or 0),
        )
        if not (profesional.nombre and profesional.telefono):
            flash("Nombre y teléfono son obligatorios.", "error")
            return render_template(
                "admin/alta_directa.html",
                oficios=Oficio.query.order_by(Oficio.nombre).all(),
                zonas=Zona.query.order_by(Zona.nombre).all(),
            )

        db.session.add(profesional)

        oficio_ids = request.form.getlist("oficios")
        zona_ids = request.form.getlist("zonas")
        if oficio_ids:
            profesional.oficios = Oficio.query.filter(Oficio.id.in_(oficio_ids)).all()
        if zona_ids:
            profesional.zonas = Zona.query.filter(Zona.id.in_(zona_ids)).all()

        db.session.commit()
        flash(f"{profesional.nombre} quedó aprobado y visible en el directorio.", "success")
        return redirect(url_for("admin.panel"))

    return render_template(
        "admin/alta_directa.html",
        oficios=Oficio.query.order_by(Oficio.nombre).all(),
        zonas=Zona.query.order_by(Zona.nombre).all(),
    )


@bp.route("/profesional/<int:profesional_id>/aprobar", methods=["POST"])
def aprobar(profesional_id):
    profesional = Profesional.query.get_or_404(profesional_id)
    profesional.estado = EstadoProfesional.APROBADO
    db.session.commit()
    return _fila_o_redirect(profesional)


@bp.route("/profesional/<int:profesional_id>/rechazar", methods=["POST"])
def rechazar(profesional_id):
    profesional = Profesional.query.get_or_404(profesional_id)
    profesional.estado = EstadoProfesional.RECHAZADO
    db.session.commit()
    return _fila_o_redirect(profesional)


def _fila_o_redirect(profesional):
    """Con htmx devolvemos solo el fragmento de la fila; sin htmx, redirigimos
    de vuelta al panel para degradación elegante.
    """
    from flask import request

    if request.headers.get("HX-Request"):
        return render_template("admin/_fila_resultado.html", profesional=profesional)
    return redirect(url_for("admin.panel"))
