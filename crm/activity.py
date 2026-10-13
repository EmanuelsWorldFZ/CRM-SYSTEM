from flask_login import current_user

from crm.extensions import db
from crm.models import ActivityLog, Client


def log_activity(
    action: str,
    target_type: str,
    target_id: int,
    client: Client,
    summary: str,
) -> None:
    db.session.add(
        ActivityLog(
            actor_id=current_user.id,
            actor_name="{} {}".format(
                current_user.first_name,
                current_user.last_name,
            ),
            owner_id=client.owner_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            client_id=client.id,
            client_name=client.name,
            summary=summary,
        )
    )
