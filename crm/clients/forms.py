from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional


class ClientForm(FlaskForm):
    name = StringField(
        "Client name",
        filters=[lambda value: value.strip() if value else value],
        validators=[DataRequired(), Length(max=160)],
    )
    company = StringField(
        "Company",
        filters=[lambda value: value.strip() or None if value else None],
        validators=[Optional(), Length(max=160)],
    )
    email = StringField(
        "Email address",
        filters=[lambda value: value.strip().lower() or None if value else None],
        validators=[Optional(), Email(), Length(max=254)],
    )
    phone = StringField(
        "Phone number",
        filters=[lambda value: value.strip() or None if value else None],
        validators=[Optional(), Length(max=40)],
    )
    submit = SubmitField("Save client")
