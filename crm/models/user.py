from datetime import datetime, timezone
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from crm.extensions import db


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(
        db.Enum(
            UserRole,
            native_enum=False,
            length=10,
            create_constraint=True,
            name="user_role",
        ),
        nullable=False,
        default=UserRole.USER,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    clients = db.relationship(
        "Client",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256:600000",
        )

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
