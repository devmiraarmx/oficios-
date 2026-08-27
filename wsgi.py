"""Punto de entrada para servidores WSGI (gunicorn) y `flask run`.

Uso local:
    flask --app wsgi run --debug

En producción (Railway) se usa el factory directamente:
    gunicorn "app:create_app()"
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
