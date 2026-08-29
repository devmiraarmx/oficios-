#!/usr/bin/env sh
# Arranque en producción (Railway).
#
# Las migraciones se corren AQUÍ, al iniciar el contenedor, no durante el
# build: en build la base de datos (red privada de Railway) todavía no es
# alcanzable. Con un pequeño reintento por si la red privada tarda en levantar.
set -e

n=0
until python -m flask --app wsgi db upgrade; do
  n=$((n + 1))
  if [ "$n" -ge 5 ]; then
    echo "db upgrade falló tras $n intentos; abortando arranque."
    exit 1
  fi
  echo "Base de datos aún no disponible; reintentando db upgrade en 3s (intento $n)..."
  sleep 3
done

exec gunicorn "app:create_app()" --bind "0.0.0.0:$PORT"
