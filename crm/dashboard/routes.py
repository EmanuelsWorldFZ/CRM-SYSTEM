from flask import render_template
from flask_login import current_user, login_required

from crm.auth.permissions import is_admin
from crm.dashboard import dashboard_blueprint
from crm.extensions import db
from crm.models import ActivityLog


@dashboard_blueprint.get("/dashboard")
@login_required
def index():
    query = db.select(ActivityLog)
    if not is_admin(current_user):
        query = query.where(ActivityLog.owner_id == current_user.id)
    activity = db.session.execute(
        query.order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc()).limit(10)
    ).scalars().all()
    return render_template(
        "dashboard/index.html",
        user=current_user,
        activity=activity,
    )
