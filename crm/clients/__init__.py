from flask import Blueprint

clients_blueprint = Blueprint(
    "clients",
    __name__,
    template_folder="../templates",
)

from crm.clients import routes  # noqa: E402,F401
