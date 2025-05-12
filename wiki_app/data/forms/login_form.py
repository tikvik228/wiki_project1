from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('ИМЯ ПОЛЬЗОВАТЕЛЯ', validators=[DataRequired()])
    password = PasswordField('ПАРОЛЬ', validators=[DataRequired()])
    remember_me = BooleanField('ЗАПОМНИТЬ МЕНЯ')
    submit = SubmitField('ВОЙТИ')