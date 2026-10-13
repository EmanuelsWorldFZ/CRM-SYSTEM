from datetime import datetime, timezone

from crm.extensions import db


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    actor_name = db.Column(db.String(161), nullable=False)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )
    action = db.Column(db.String(40), nullable=False)
    target_type = db.Column(db.String(40), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    client_id = db.Column(db.Integer, index=True)
    client_name = db.Column(db.String(160), nullable=False)
    summary = db.Column(db.String(240), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
