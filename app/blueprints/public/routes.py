"""Rutas públicas: landing, landing SEO oficio × ciudad, directorio,
perfil de profesional y formulario de solicitud.

En esta primera iteración las vistas renderizan datos reales cuando existen
en la base; el flujo de verificación por SMS, el pago del lead y el push se
conectan en iteraciones siguientes (ver TODOs).
"""
from flask import render_template, request, redirect, url_for, flash, current_app

from app.blueprints.public import bp
from app.extensions import db
from app.models import (
    Oficio,
    Zona,
    Profesional,
    Solicitud,
    Urgencia,
    EstadoProfesional,
)


@bp.route("/")
def inicio():
    # El catálogo agrupado lo arma la plantilla con catalogo_por_seccion().
    return render_template("public/inicio.html")


@bp.route("/cimant")
def ancla_cimant():
    """Página ancla de CIMANT: el cliente elige servicio, alcaldía y urgencia,
    y continúa en WhatsApp; el especialista se asigna manualmente desde ahí.
    """
    digitos = "".join(c for c in current_app.config.get("WHATSAPP_NEGOCIO", "") if c.isdigit())
    if len(digitos) == 10:  # número nacional MX sin lada de país
        digitos = "52" + digitos
    return render_template(
        "public/ancla_cimant.html",
        whatsapp=digitos,
        borrador=current_app.config.get("ANCLA_BORRADOR", True),
    )


@bp.route("/oficio/<oficio_slug>/<zona_slug>")
def landing_oficio_zona(oficio_slug, zona_slug):
    """Landing SEO renderizada en servidor: 'plomero en Coyoacán'.
    Indexable, con los profesionales aprobados que cubren ese oficio y zona.
    """
    oficio = Oficio.query.filter_by(slug=oficio_slug).first_or_404()
    zona = Zona.query.filter_by(slug=zona_slug).first_or_404()

    profesionales = (
        Profesional.query.filter(Profesional.estado == EstadoProfesional.APROBADO)
        .filter(Profesional.oficios.any(id=oficio.id))
        .filter(Profesional.zonas.any(id=zona.id))
        .all()
    )
    return render_template(
        "public/landing_oficio_zona.html",
        oficio=oficio,
        zona=zona,
        profesionales=profesionales,
    )


@bp.route("/directorio")
def directorio():
    """Directorio filtrable por oficio y zona (query params ?oficio=&zona=)."""
    q = Profesional.query.filter(Profesional.estado == EstadoProfesional.APROBADO)

    oficio_slug = request.args.get("oficio")
    zona_slug = request.args.get("zona")
    if oficio_slug:
        q = q.filter(Profesional.oficios.any(slug=oficio_slug))
    if zona_slug:
        q = q.filter(Profesional.zonas.any(slug=zona_slug))

    profesionales = q.all()
    return render_template(
        "public/directorio.html",
        profesionales=profesionales,
        zonas=Zona.query.order_by(Zona.nombre).all(),
        oficio_sel=oficio_slug,
        zona_sel=zona_slug,
    )


@bp.route("/profesional/<int:profesional_id>")
def perfil_profesional(profesional_id):
    """Perfil público. El teléfono NUNCA se muestra aquí: permanece oculto
    hasta que un profesional paga por el lead (modelo tipo Cronoshare).
    """
    profesional = Profesional.query.filter_by(
        id=profesional_id, estado=EstadoProfesional.APROBADO
    ).first_or_404()
    return render_template("public/perfil.html", profesional=profesional)


@bp.route("/solicitar", methods=["GET", "POST"])
def solicitar():
    """Formulario de solicitud del cliente: sin registro, cero fricción.
    Al enviar se crea la solicitud; el teléfono se marca como NO verificado
    hasta pasar por Twilio Verify (siguiente iteración).
    """
    if request.method == "POST":
        solicitud = Solicitud(
            oficio=request.form.get("oficio", "").strip(),
            zona=request.form.get("zona", "").strip(),
            descripcion=request.form.get("descripcion", "").strip(),
            urgencia=request.form.get("urgencia", Urgencia.SIN_PRISA.value),
            nombre_cliente=request.form.get("nombre", "").strip(),
            telefono_cliente=request.form.get("telefono", "").strip(),
            telefono_verificado=False,
        )
        if not (solicitud.oficio and solicitud.zona and solicitud.descripcion
                and solicitud.telefono_cliente):
            flash("Por favor completa oficio, zona, descripción y teléfono.", "error")
            return render_template("public/solicitar.html",
                                   oficios=Oficio.query.order_by(Oficio.nombre).all())

        # En modo demo saltamos la verificación por SMS (Twilio aún no está) y
        # damos la solicitud por verificada, para que llegue de inmediato a la
        # bandeja del profesional durante una demostración en vivo.
        if current_app.config.get("DEMO_MODE"):
            solicitud.telefono_verificado = True

        db.session.add(solicitud)
        db.session.commit()

        # TODO: disparar verificación por SMS (Twilio Verify). Cuando la
        # solicitud queda verificada se notifica a los profesionales que
        # coincidan (esto ya se activa aquí y con Twilio será el mismo camino).
        if solicitud.telefono_verificado:
            from app.notificaciones import notificar_nuevo_lead
            notificar_nuevo_lead(solicitud)
        return redirect(url_for("public.solicitud_recibida", solicitud_id=solicitud.id))

    return render_template(
        "public/solicitar.html",
        oficios=Oficio.query.order_by(Oficio.nombre).all(),
    )


@bp.route("/solicitud/<int:solicitud_id>/recibida")
def solicitud_recibida(solicitud_id):
    solicitud = Solicitud.query.get_or_404(solicitud_id)
    return render_template("public/solicitud_recibida.html", solicitud=solicitud)


@bp.route("/aviso-de-privacidad")
def aviso_privacidad():
    """Obligación LFPDPPP al recabar nombre y teléfono del cliente."""
    return render_template("public/aviso_privacidad.html")
