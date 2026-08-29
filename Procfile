web: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT
release: sh -c "FLASK_APP=wsgi flask db upgrade"
