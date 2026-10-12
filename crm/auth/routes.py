from __future__ import annotations

from urllib.parse import urlsplit

from sqlalchemy.exc import IntegrityError
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from crm.auth import auth_blueprint
from crm.auth.forms import LoginForm, RegistrationForm
from crm.extensions import db
from crm.models import User


def _safe_next_url(target: str | None) -> str | None:
    if not target or not target.startswith("/") or target.startswith("//"):
        return None

    parsed_target = urlsplit(target)
    if parsed_target.scheme or parsed_target.netloc or "\\" in target:
        return None
    return target


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.welcome"))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        ).scalar_one_or_none()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
        else:
            login_user(user)
            flash("You are now logged in.", "success")
            return redirect(
                _safe_next_url(request.args.get("next"))
                or url_for("auth.welcome")
            )

    return render_template("auth/login.html", form=form)


@auth_blueprint.get("/welcome")
@login_required
def welcome():
    return render_template("auth/welcome.html")


@auth_blueprint.post("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = db.session.execute(
            db.select(User).where(User.email == form.email.data)
        ).scalar_one_or_none()
        if existing_user is not None:
            form.email.errors.append("An account with that email already exists.")
        else:
            user = User(
                first_name=form.first_name.data.strip(),
                last_name=form.last_name.data.strip(),
                email=form.email.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                form.email.errors.append(
                    "An account with that email already exists."
                )
            else:
                flash("Your account has been created. You can log in next.", "success")
                return redirect(url_for("auth.registration_success"))

    return render_template("auth/register.html", form=form)


@auth_blueprint.get("/registered")
def registration_success():
    return render_template("auth/registration_success.html")
