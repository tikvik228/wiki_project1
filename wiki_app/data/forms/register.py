from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField
from wtforms.validators import DataRequired, Length


class RegisterForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired(), Length(max=120)])
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(max=60)])
    about = StringField('Напишите немного о себе:', validators=[DataRequired(), Length(max=300)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')