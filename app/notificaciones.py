"""Notificaciones Web Push (pywebpush + VAPID).

Envía un push a los profesionales cuando llega un lead válido que coincide con
su oficio y zona. Las llaves VAPID se configuran por entorno; si no están,
el envío se omite en silencio (útil en local sin configurar nada).

Genera un par de llaves con:  flask vapid-keys
"""
import base64
import json
import logging

from flask import current_app

from app.extensions import db
from app.models import SuscripcionPush
from app.servicios import profesionales_para_solicitud

log = logging.getLogger(__name__)


def _vapid_configurado() -> bool:
    return bool(
        current_app.config.get("VAPID_PRIVATE_KEY")
        and current_app.config.get("VAPID_PUBLIC_KEY")
    )


def clave_publica() -> str | None:
    """Application server key (base64url) que el navegador usa para suscribirse."""
    return current_app.config.get("VAPID_PUBLIC_KEY")


def enviar_push(suscripcion: SuscripcionPush, payload: dict) -> bool:
    """Envía un push a una suscripción. Devuelve True si se entregó.
    Si la suscripción ya no existe (410/404), la elimina."""
    if not _vapid_configurado():
        log.info("VAPID sin configurar; se omite el push.")
        return False

    from pywebpush import webpush, WebPushException

    try:
        webpush(
            subscription_info=suscripcion.info(),
            data=json.dumps(payload),
            vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
            vapid_claims={"sub": current_app.config["VAPID_CLAIM_EMAIL"]},
        )
        return True
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        if status in (404, 410):
            # Suscripción caducada o cancelada: se limpia.
            db.session.delete(suscripcion)
            db.session.commit()
            log.info("Suscripción push eliminada (status %s).", status)
        else:
            log.warning("Fallo al enviar push: %s", exc)
        return False


def notificar_nuevo_lead(solicitud) -> int:
    """Notifica a los profesionales que coinciden con la solicitud.
    Devuelve cuántos envíos se realizaron con éxito."""
    payload = {
        "titulo": f"Nuevo lead: {solicitud.oficio} en {solicitud.zona}",
        "cuerpo": (solicitud.descripcion or "")[:120],
        "url": "/",  # el enlace concreto se arma por profesional abajo
    }
    enviados = 0
    for profesional in profesionales_para_solicitud(solicitud):
        payload_prof = dict(
            payload,
            url=f"/profesionales/{profesional.token_acceso}/leads",
        )
        for suscripcion in profesional.suscripciones_push:
            if enviar_push(suscripcion, payload_prof):
                enviados += 1
    return enviados


def notificar_derivacion(profesional, solicitud) -> int:
    """Avisa a un profesional que el equipo le derivó un lead directamente.
    Devuelve cuántos envíos se realizaron con éxito (0 si push sin configurar)."""
    payload = {
        "titulo": f"Te derivamos un lead: {solicitud.oficio} en {solicitud.zona}",
        "cuerpo": (solicitud.descripcion or "")[:120],
        "url": f"/profesionales/{profesional.token_acceso}/leads",
    }
    enviados = 0
    for suscripcion in profesional.suscripciones_push:
        if enviar_push(suscripcion, payload):
            enviados += 1
    return enviados


# --------------------------------------------------------------------------
# Generación de llaves VAPID (base64url de una línea, aptas para .env)
# --------------------------------------------------------------------------
def generar_llaves_vapid() -> tuple[str, str]:
    """Devuelve (public_key, private_key) en base64url sin padding."""
    from cryptography.hazmat.primitives import serialization
    from py_vapid import Vapid01

    v = Vapid01()
    v.generate_keys()

    priv_raw = v.private_key.private_numbers().private_value.to_bytes(32, "big")
    pub_raw = v.public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    return b64(pub_raw), b64(priv_raw)
