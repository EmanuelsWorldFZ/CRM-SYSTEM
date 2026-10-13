from flask import Blueprint

dashboard_blueprint = Blueprint(
    "dashboard",
    __name__,
    template_folder="../templates",
)

from crm.dashboard import routes  # noqa: E402,F401
