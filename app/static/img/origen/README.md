# Original de los iconos

Deja aquí tu imagen original y corre el generador:

```bash
python scripts/generar_iconos.py
```

## Qué dejar

- `logo.png` — **requerido**. Cuadrado, mínimo 1024×1024 px, fondo
  transparente. De aquí se generan todos los tamaños PWA + favicons.
- `logo.svg` — *opcional*. Si lo pones, se copia como `favicon.svg`
  (favicon vectorial moderno, nítido en cualquier resolución).

También puedes pasar la ruta directo:

```bash
python scripts/generar_iconos.py ruta/a/mi-logo.png
```

Los archivos generados van a `app/static/img/` (una carpeta arriba) y **sí**
se versionan. Esta carpeta `origen/` guarda solo la fuente.
