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
    Solicitud,
    EstadoProfesional,
    OrigenProfesional,
)
from app.servicios import (
    derivar_lead,
    profesionales_para_solicitud,
)


@bp.route("/")
def panel():
    pendientes = (
        Profesional.query.filter_by(estado=EstadoProfesional.PENDIENTE)
        .order_by(Profesional.creado_en.asc())
        .all()
    )
    aprobados = (
        Profesional.query.filter_by(estado=EstadoProfesional.APROBADO)
        .order_by(Profesional.creado_en.desc())
        .all()
    )
    return render_template("admin/panel.html", pendientes=pendientes, aprobados=aprobados)


@bp.route("/solicitudes")
def solicitudes():
    """Todas las solicitudes de servicio recibidas (leads), más recientes
    primero. Desde aquí el equipo puede derivar cada una a un profesional."""
    todas = Solicitud.query.order_by(Solicitud.creado_en.desc()).all()
    aprobados = (
        Profesional.query.filter_by(estado=EstadoProfesional.APROBADO)
        .order_by(Profesional.nombre).all()
    )
    # Por solicitud: profesionales que coinciden (sugerencia) y a quién ya se
    # derivó (para no repetir y mostrarlo).
    coincidencias = {s.id: profesionales_para_solicitud(s) for s in todas}
    ya_derivadas = {
        s.id: [d.profesional.nombre for d in s.derivaciones] for s in todas
    }
    return render_template(
        "admin/solicitudes.html",
        solicitudes=todas,
        aprobados=aprobados,
        coincidencias=coincidencias,
        ya_derivadas=ya_derivadas,
    )


@bp.route("/solicitud/<int:solicitud_id>/derivar", methods=["POST"])
def derivar(solicitud_id):
    """Deriva una solicitud a un profesional aprobado (asignación manual)."""
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    profesional_id = request.form.get("profesional_id")
    profesional = Profesional.query.filter_by(
        id=profesional_id, estado=EstadoProfesional.APROBADO
    ).first()
    if profesional is None:
        flash("Selecciona un profesional aprobado para derivar la solicitud.", "error")
        return redirect(url_for("admin.solicitudes"))

    _derivacion, creada = derivar_lead(profesional, solicitud)
    if creada:
        # Aviso push best-effort (si el profesional tiene notificaciones activas).
        try:
            from app.notificaciones import notificar_derivacion
            notificar_derivacion(profesional, solicitud)
        except Exception:  # nunca romper la derivación por un fallo de push
            pass
        flash(
            f"Solicitud derivada a {profesional.nombre}. La verá en su bandeja "
            f"de leads sin costo.",
            "success",
        )
    else:
        flash(f"Esa solicitud ya estaba derivada a {profesional.nombre}.", "success")
    return redirect(url_for("admin.solicitudes"))


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

        from app.almacenamiento import guardar_imagen, ImagenInvalida
        try:
            url_foto = guardar_imagen(request.files.get("foto"))
            if url_foto:
                profesional.foto_url = url_foto
        except ImagenInvalida as e:
            flash(str(e), "error")
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
        enlace = url_for("profesionales.leads", token=profesional.token_acceso)
        flash(
            f"{profesional.nombre} quedó aprobado y visible en el directorio. "
            f"Envíale su enlace de leads: {enlace}",
            "success",
        )
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
