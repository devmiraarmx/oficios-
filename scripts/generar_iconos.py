#!/usr/bin/env python3
"""Genera todos los iconos de la PWA y los favicons a partir de un solo original.

Uso:
    python scripts/generar_iconos.py app/static/img/origen/logo.png

También detecta automáticamente el original si lo dejas en
`app/static/img/origen/` con nombre `logo.png`, `logo.jpg` o `logo.webp`.

Recomendado: original cuadrado de al menos 1024x1024 px, con fondo transparente
(PNG). Si además dejas un `logo.svg` en la misma carpeta, se copia como favicon
vectorial moderno (favicon.svg).

Salidas en app/static/img/ :
    favicon.ico            (16/32/48, para navegadores viejos)
    favicon-16.png
    favicon-32.png
    favicon.svg            (solo si existe un logo.svg de origen)
    icono-192.png          (PWA, purpose "any")
    icono-512.png          (PWA, purpose "any")
    icono-maskable-512.png (PWA, purpose "maskable", con zona segura)
    apple-touch-icon.png   (180x180, con fondo sólido; iOS no usa transparencia)
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
DIR_IMG = RAIZ / "app" / "static" / "img"
DIR_ORIGEN = DIR_IMG / "origen"

# Color papel del sistema de diseño (fondo para apple-touch-icon).
FONDO_PAPEL = (247, 245, 240, 255)  # #F7F5F0


def encontrar_original(arg: str | None) -> Path:
    if arg:
        p = Path(arg)
        if not p.is_absolute():
            p = RAIZ / p
        if not p.exists():
            sys.exit(f"No existe el archivo: {p}")
        return p
    for nombre in ("logo.png", "logo.webp", "logo.jpg", "logo.jpeg"):
        cand = DIR_ORIGEN / nombre
        if cand.exists():
            return cand
    sys.exit(
        "No encontré el original. Deja tu imagen en "
        f"{DIR_ORIGEN}/logo.png (o pásala como argumento)."
    )


def cargar_cuadrado(ruta: Path) -> Image.Image:
    """Abre el original y lo deja cuadrado (RGBA) sin deformarlo."""
    img = Image.open(ruta).convert("RGBA")
    w, h = img.size
    if w != h:
        lado = max(w, h)
        lienzo = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
        lienzo.paste(img, ((lado - w) // 2, (lado - h) // 2), img)
        img = lienzo
    return img


def redimensionar(img: Image.Image, lado: int) -> Image.Image:
    return img.resize((lado, lado), Image.LANCZOS)


def guardar_png(img: Image.Image, nombre: str) -> None:
    destino = DIR_IMG / nombre
    img.save(destino, "PNG", optimize=True)
    print(f"  ✓ {destino.relative_to(RAIZ)}  ({img.size[0]}x{img.size[1]})")


def generar_maskable(img: Image.Image, lado: int = 512) -> Image.Image:
    """Maskable: el contenido debe caber en el ~80% central (zona segura).

    Los launchers recortan los bordes (círculo, cuadrado redondeado, etc.),
    así que dejamos margen y ponemos fondo papel sólido para que no se vea
    transparencia recortada.
    """
    lienzo = Image.new("RGBA", (lado, lado), FONDO_PAPEL)
    contenido = int(lado * 0.80)
    logo = redimensionar(img, contenido)
    off = (lado - contenido) // 2
    lienzo.paste(logo, (off, off), logo)
    return lienzo


def generar_apple(img: Image.Image, lado: int = 180) -> Image.Image:
    """Apple no maneja bien la transparencia: fondo papel sólido."""
    lienzo = Image.new("RGBA", (lado, lado), FONDO_PAPEL)
    logo = redimensionar(img, lado)
    lienzo.paste(logo, (0, 0), logo)
    return lienzo.convert("RGB")


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    original = encontrar_original(arg)
    print(f"Original: {original.relative_to(RAIZ)}")
    img = cargar_cuadrado(original)
    if img.size[0] < 512:
        print(
            f"  ⚠ El original mide {img.size[0]}px; se recomienda >=1024px "
            "para que icono-512 no se vea borroso."
        )

    print("Generando iconos PWA:")
    guardar_png(redimensionar(img, 192), "icono-192.png")
    guardar_png(redimensionar(img, 512), "icono-512.png")
    guardar_png(generar_maskable(img, 512), "icono-maskable-512.png")

    print("Generando favicons:")
    guardar_png(redimensionar(img, 16), "favicon-16.png")
    guardar_png(redimensionar(img, 32), "favicon-32.png")
    ico = DIR_IMG / "favicon.ico"
    redimensionar(img, 48).save(
        ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)]
    )
    print(f"  ✓ {ico.relative_to(RAIZ)}  (16/32/48)")

    print("Generando apple-touch-icon:")
    guardar_png(generar_apple(img, 180), "apple-touch-icon.png")

    svg_origen = DIR_ORIGEN / "logo.svg"
    if svg_origen.exists():
        shutil.copyfile(svg_origen, DIR_IMG / "favicon.svg")
        print(f"  ✓ {(DIR_IMG / 'favicon.svg').relative_to(RAIZ)}  (vectorial)")
    else:
        print("  (sin logo.svg de origen: se omite favicon.svg vectorial)")

    print("\nListo. Revisa app/static/img/ y haz commit de los archivos.")


if __name__ == "__main__":
    main()
