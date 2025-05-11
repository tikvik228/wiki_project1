from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, FileField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileAllowed


class UserForm(FlaskForm):
    username = StringField('юзернейм', validators=[DataRequired(), Length(max=60)])
    email = StringField('почта', validators=[DataRequired(),  Length(max=120)])
    image_file = FileField('Изображение (png, jpg)', validators=[FileAllowed(['jpg', 'png']) ])
    about = StringField('о себе', validators=[DataRequired(), Length(max=300)])
    submit = SubmitField('СОХРАНИТЬ')