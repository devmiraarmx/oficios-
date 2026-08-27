from flask import Blueprint

bp = Blueprint("public", __name__, template_folder="../../templates/public")

from app.blueprints.public import routes  # noqa: E402,F401
