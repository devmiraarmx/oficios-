"""Instancias de extensiones, separadas del factory para evitar imports
circulares. Se inicializan en `create_app()`.
"""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
