from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegistrationForm(FlaskForm):
    first_name = StringField(
        "First name",
        validators=[DataRequired(), Length(max=80)],
    )
    last_name = StringField(
        "Last name",
        validators=[DataRequired(), Length(max=80)],
    )
    email = StringField(
        "Email address",
        filters=[lambda value: value.strip().lower() if value else value],
        validators=[DataRequired(), Email(), Length(max=254)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=12, max=128)],
    )
    password_confirmation = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField(
        "Email address",
        filters=[lambda value: value.strip().lower() if value else value],
        validators=[DataRequired(), Email(), Length(max=254)],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(max=128)],
    )
    submit = SubmitField("Log in")
