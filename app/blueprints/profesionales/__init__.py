from flask import Blueprint

bp = Blueprint("profesionales", __name__, template_folder="../../templates/profesionales")

from app.blueprints.profesionales import routes  # noqa: E402,F401
