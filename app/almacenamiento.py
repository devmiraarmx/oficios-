"""Almacenamiento de imágenes (foto de perfil del profesional).

Usa Cloudinary cuando hay credenciales (CLOUDINARY_URL); si no, guarda en
disco local bajo static/uploads/ para poder trabajar sin cuenta. Devuelve la
URL pública lista para usar en <img src=...>.
"""
import os
import uuid

from flask import current_app, url_for

EXTENSIONES_PERMITIDAS = {"png", "jpg", "jpeg", "webp", "gif"}


class ImagenInvalida(Exception):
    """El archivo no es una imagen con extensión permitida."""


def _extension(nombre: str) -> str:
    return nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""


def guardar_imagen(archivo, carpeta: str = "perfiles") -> str | None:
    """Guarda la imagen y devuelve su URL pública.

    `archivo` es un FileStorage de Flask (request.files[...]). Si viene vacío
    devuelve None (campo opcional). Lanza ImagenInvalida si la extensión no
    está permitida.
    """
    if archivo is None or not getattr(archivo, "filename", ""):
        return None

    ext = _extension(archivo.filename)
    if ext not in EXTENSIONES_PERMITIDAS:
        raise ImagenInvalida(
            "Formato no permitido. Usa JPG, PNG, WEBP o GIF."
        )

    if current_app.config.get("CLOUDINARY_URL"):
        return _subir_cloudinary(archivo, carpeta)
    return _guardar_local(archivo, carpeta, ext)


def _subir_cloudinary(archivo, carpeta: str) -> str:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config()  # lee CLOUDINARY_URL del entorno
    resultado = cloudinary.uploader.upload(
        archivo, folder=f"oficios/{carpeta}"
    )
    return resultado["secure_url"]


def _guardar_local(archivo, carpeta: str, ext: str) -> str:
    nombre = f"{uuid.uuid4().hex}.{ext}"
    destino_dir = os.path.join(current_app.static_folder, "uploads", carpeta)
    os.makedirs(destino_dir, exist_ok=True)
    archivo.save(os.path.join(destino_dir, nombre))
    return url_for("static", filename=f"uploads/{carpeta}/{nombre}")
