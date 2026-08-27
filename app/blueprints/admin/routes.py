"""Panel de administración simple: cola de altas pendientes con
aprobar/rechazar. Sin roles ni permisos — es solo para el founder y su socio.

Las acciones usan htmx: al aprobar/rechazar se devuelve solo la fila
actualizada, sin recargar la página.
"""
from flask import render_template, redirect, url_for

from app.blueprints.admin import bp
from app.extensions import db
from app.models import Profesional, EstadoProfesional


@bp.route("/")
def panel():
    pendientes = (
        Profesional.query.filter_by(estado=EstadoProfesional.PENDIENTE)
        .order_by(Profesional.creado_en.asc())
        .all()
    )
    return render_template("admin/panel.html", pendientes=pendientes)


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
