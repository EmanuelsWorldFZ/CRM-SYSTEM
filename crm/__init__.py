from __future__ import annotations

from pathlib import Path

import click
from flask import Flask, redirect, url_for
from flask_login import current_user

from crm.config import Config
from crm.extensions import csrf, db, login_manager
from crm.models import User, UserRole


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Set SECRET_KEY in the environment before starting the app.")

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        try:
            user_id_int = int(user_id)
        except ValueError:
            return None
        return db.session.get(User, user_id_int)

    from crm.auth import auth_blueprint
    from crm.api import api_blueprint
    from crm.clients import clients_blueprint
    from crm.dashboard import dashboard_blueprint

    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(api_blueprint, url_prefix="/api/v1")
    app.register_blueprint(clients_blueprint, url_prefix="/clients")
    app.register_blueprint(dashboard_blueprint)

    @app.get("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("auth.login"))

    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Create the application's database tables."""
        with app.app_context():
            db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("set-user-role")
    @click.argument("email")
    @click.argument(
        "role",
        type=click.Choice([role.value for role in UserRole], case_sensitive=False),
    )
    def set_user_role_command(email: str, role: str) -> None:
        """Set an existing user's role from a trusted administrative shell."""
        normalized_email = email.strip().lower()
        user = db.session.execute(
            db.select(User).where(User.email == normalized_email)
        ).scalar_one_or_none()
        if user is None:
            raise click.ClickException("No user found with that email address.")

        user.role = UserRole(role.lower())
        db.session.commit()
        click.echo("Updated {} to role {}.".format(user.email, user.role.value))

    return app
