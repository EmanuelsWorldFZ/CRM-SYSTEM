from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class NoteForm(FlaskForm):
    body = TextAreaField(
        "Note",
        filters=[lambda value: value.strip() if value else value],
        validators=[DataRequired(), Length(max=5000)],
    )
    submit = SubmitField("Add note")
