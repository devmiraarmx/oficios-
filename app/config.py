"""Configuración de la aplicación.

Lee variables de entorno (.env en local, panel de Railway en producción).
"""
import os
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()


def _es_verdadero(valor: str | None) -> bool:
    return (valor or "").strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


def _parsear_instante(valor: str | None) -> datetime | None:
    """Convierte una fecha/hora ISO 8601 en un `datetime` con zona horaria.

    Se usa para programar el modo descanso. Acepta un desfase explícito
    (ej. `2026-09-01T00:00:00-06:00`, que es medianoche en CDMX/Cancún). Si
    la cadena no trae zona horaria, se asume UTC. Un valor vacío o inválido
    devuelve `None` (modo descanso apagado), para que un typo nunca tire la
    app: se registra y se ignora.
    """
    if not valor or not valor.strip():
        return None
    try:
        instante = datetime.fromisoformat(valor.strip())
    except ValueError:
        return None
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=timezone.utc)
    return instante


def _normalizar_url_bd(url: str | None) -> str:
    """Railway/Heroku a veces entregan la URL como `postgres://`.
    SQLAlchemy espera `postgresql://`. Si no hay URL, cae a SQLite local
    para poder arrancar sin configurar nada.
    """
    if not url:
        return "sqlite:///oficios_dev.sqlite3"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-inseguro-cambiar-en-produccion")

    SQLALCHEMY_DATABASE_URI = _normalizar_url_bd(os.getenv("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Tamaño máximo de subida (foto de perfil). 5 MB.
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Modo demo: salta la verificación por SMS (Twilio aún no conectado) y marca
    # las solicitudes como verificadas al crearse, para que aparezcan de
    # inmediato en la bandeja del profesional. SOLO para mostrar el flujo
    # completo; en producción real debe quedar apagado.
    DEMO_MODE = _es_verdadero(os.getenv("DEMO_MODE"))

    # Modo descanso programado: a partir de este instante la app pública
    # responde con una página "En mantenimiento" (HTTP 503) en vez del sitio
    # normal. El panel de admin y el health check siguen accesibles. Se activa
    # poniendo la variable de entorno; se apaga quitándola (descanso indefinido
    # hasta reactivar). Ver README.
    #   Ejemplo: MODO_DESCANSO_DESDE=2026-09-01T00:00:00-06:00
    MODO_DESCANSO_DESDE = _parsear_instante(os.getenv("MODO_DESCANSO_DESDE"))
    MODO_DESCANSO_MENSAJE = os.getenv(
        "MODO_DESCANSO_MENSAJE",
        "Estamos tomando un descanso. Volvemos pronto.",
    )

    # Créditos: cuántos se descuentan al desbloquear un lead.
    CREDITOS_POR_LEAD = 1

    # Paquetes de créditos con precio decreciente por volumen (ver CLAUDE.md).
    # precio_mxn es el total del paquete; el precio unitario baja al subir el
    # volumen. Son valores ilustrativos, ajustables sin tocar código.
    PAQUETES_CREDITOS = [
        {"creditos": 5, "precio_mxn": 250, "popular": False},
        {"creditos": 10, "precio_mxn": 450, "popular": True},
        {"creditos": 20, "precio_mxn": 800, "popular": False},
    ]

    # Integraciones externas (ver CLAUDE.md). Vacías = módulo desactivado.
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_VERIFY_SERVICE_SID = os.getenv("TWILIO_VERIFY_SERVICE_SID")

    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

    CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")

    VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
    VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
    VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL", "mailto:contacto@ejemplo.mx")
