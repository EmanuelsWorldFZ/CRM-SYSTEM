from flask import render_template
from flask_login import current_user, login_required

from crm.dashboard import dashboard_blueprint


@dashboard_blueprint.get("/dashboard")
@login_required
def index():
    return render_template("dashboard/index.html", user=current_user)
