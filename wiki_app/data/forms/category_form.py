from flask_wtf import FlaskForm
from wtforms import  StringField, SubmitField
from wtforms.validators import DataRequired


class CategForm(FlaskForm):
    name = StringField('название категории', validators=[DataRequired()])
    submit = SubmitField('СОХРАНИТЬ')