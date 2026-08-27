"""Rutas públicas: landing, landing SEO oficio × ciudad, directorio,
perfil de profesional y formulario de solicitud.

En esta primera iteración las vistas renderizan datos reales cuando existen
en la base; el flujo de verificación por SMS, el pago del lead y el push se
conectan en iteraciones siguientes (ver TODOs).
"""
from flask import render_template, request, redirect, url_for, flash

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
    oficios = Oficio.query.order_by(Oficio.nombre).all()
    return render_template("public/inicio.html", oficios=oficios)


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
        oficios=Oficio.query.order_by(Oficio.nombre).all(),
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

        db.session.add(solicitud)
        db.session.commit()
        # TODO: disparar verificación por SMS (Twilio Verify) y, una vez
        # verificado, notificar por push a los profesionales que coincidan.
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
