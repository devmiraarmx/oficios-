"""Configuración de la aplicación.

Lee variables de entorno (.env en local, panel de Railway en producción).
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _es_verdadero(valor: str | None) -> bool:
    return (valor or "").strip().lower() in {"1", "true", "yes", "on", "si", "sí"}


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
