"""Rutas del profesional: alta/registro, bandeja de leads, desbloqueo de
contacto (cobro de un crédito) y compra de créditos.

MVP sin login: el acceso a la bandeja es por enlace mágico (token en la URL),
no hay contraseña. El alta pública entra a la cola de verificación manual.
"""
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    abort,
)

from app.blueprints.profesionales import bp
from app.extensions import db
from app.models import Profesional, Oficio, Zona, EstadoProfesional
from app.servicios import (
    desbloquear_lead,
    acreditar_compra,
    leads_para,
    ids_desbloqueadas,
    CreditosInsuficientes,
)


def _profesional_por_token(token: str) -> Profesional:
    """Carga al profesional por su enlace mágico. Solo aprobados tienen
    bandeja activa."""
    return Profesional.query.filter_by(
        token_acceso=token, estado=EstadoProfesional.APROBADO
    ).first_or_404()


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

        # Foto de perfil (opcional)
        from app.almacenamiento import guardar_imagen, ImagenInvalida
        try:
            url_foto = guardar_imagen(request.files.get("foto"))
            if url_foto:
                profesional.foto_url = url_foto
        except ImagenInvalida as e:
            flash(str(e), "error")
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


# --------------------------------------------------------------------------
# Bandeja de leads y desbloqueo (acceso por enlace mágico, sin login)
# --------------------------------------------------------------------------
@bp.route("/<token>/leads")
def leads(token):
    profesional = _profesional_por_token(token)
    leads = leads_para(profesional)
    desbloqueadas = ids_desbloqueadas(profesional)
    return render_template(
        "profesionales/leads.html",
        profesional=profesional,
        leads=leads,
        desbloqueadas=desbloqueadas,
        creditos_por_lead=current_app.config["CREDITOS_POR_LEAD"],
    )


@bp.route("/<token>/desbloquear/<int:solicitud_id>", methods=["POST"])
def desbloquear(token, solicitud_id):
    profesional = _profesional_por_token(token)
    from app.models import Solicitud

    solicitud = Solicitud.query.get_or_404(solicitud_id)
    if not solicitud.telefono_verificado:
        abort(400)  # solo los leads verificados son válidos

    try:
        desbloquear_lead(
            profesional, solicitud,
            creditos_por_lead=current_app.config["CREDITOS_POR_LEAD"],
        )
    except CreditosInsuficientes:
        # Con htmx devolvemos el bloque de "sin créditos"; sin htmx redirigimos
        # a la página de compra.
        if request.headers.get("HX-Request"):
            return render_template(
                "profesionales/_sin_creditos.html",
                profesional=profesional, solicitud=solicitud,
            ), 402
        return redirect(url_for("profesionales.creditos", token=token))

    # Éxito: revelamos el contacto. Con htmx solo el fragmento de contacto.
    if request.headers.get("HX-Request"):
        return render_template(
            "profesionales/_contacto.html",
            profesional=profesional, solicitud=solicitud,
        )
    return redirect(url_for("profesionales.leads", token=token))


# --------------------------------------------------------------------------
# Compra de créditos (pago simulado; Stripe/Conekta se conecta después)
# --------------------------------------------------------------------------
@bp.route("/<token>/creditos")
def creditos(token):
    profesional = _profesional_por_token(token)
    return render_template(
        "profesionales/creditos.html",
        profesional=profesional,
        paquetes=current_app.config["PAQUETES_CREDITOS"],
    )


@bp.route("/<token>/creditos/comprar/<int:indice>", methods=["POST"])
def comprar_creditos(token, indice):
    profesional = _profesional_por_token(token)
    paquetes = current_app.config["PAQUETES_CREDITOS"]
    if indice < 0 or indice >= len(paquetes):
        abort(404)
    paquete = paquetes[indice]

    # TODO: crear la sesión de pago (Stripe/Conekta) y acreditar en el webhook
    # tras confirmar el pago. Por ahora acreditamos directo para probar el flujo.
    acreditar_compra(profesional, paquete["creditos"])
    flash(
        f"Se acreditaron {paquete['creditos']} créditos (pago simulado). "
        f"Saldo actual: {profesional.saldo_creditos}.",
        "success",
    )
    return redirect(url_for("profesionales.creditos", token=token))


# --------------------------------------------------------------------------
# Suscripción a notificaciones Web Push
# --------------------------------------------------------------------------
@bp.route("/<token>/push/clave-publica")
def push_clave_publica(token):
    _profesional_por_token(token)
    from app.notificaciones import clave_publica

    clave = clave_publica()
    if not clave:
        return {"habilitado": False}, 200
    return {"habilitado": True, "clave": clave}, 200


@bp.route("/<token>/push/suscribir", methods=["POST"])
def push_suscribir(token):
    profesional = _profesional_por_token(token)
    from app.models import SuscripcionPush

    datos = request.get_json(silent=True) or {}
    endpoint = datos.get("endpoint")
    claves = datos.get("keys") or {}
    p256dh, auth = claves.get("p256dh"), claves.get("auth")
    if not (endpoint and p256dh and auth):
        return {"ok": False, "error": "suscripción incompleta"}, 400

    # Upsert por endpoint (evita duplicados si se resuscribe el mismo navegador).
    suscripcion = SuscripcionPush.query.filter_by(endpoint=endpoint).first()
    if suscripcion is None:
        suscripcion = SuscripcionPush(endpoint=endpoint)
        db.session.add(suscripcion)
    suscripcion.profesional_id = profesional.id
    suscripcion.p256dh = p256dh
    suscripcion.auth = auth
    db.session.commit()
    return {"ok": True}, 201


@bp.route("/<token>/push/baja", methods=["POST"])
def push_baja(token):
    _profesional_por_token(token)
    from app.models import SuscripcionPush

    datos = request.get_json(silent=True) or {}
    endpoint = datos.get("endpoint")
    if endpoint:
        SuscripcionPush.query.filter_by(endpoint=endpoint).delete()
        db.session.commit()
    return {"ok": True}, 200
