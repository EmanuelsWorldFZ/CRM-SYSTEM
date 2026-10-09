from sqlalchemy.exc import IntegrityError
from flask import flash, redirect, render_template, url_for

from crm.auth import auth_blueprint
from crm.auth.forms import RegistrationForm
from crm.extensions import db
from crm.models import User


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
