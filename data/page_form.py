from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField
from data.db_session import create_session
from data.categories import Category

def func_categ():
    db_sess = create_session()
    try:
        return db_sess.query(Category).all()
    finally:
        db_sess.close()

class PageForm(FlaskForm):
    title = StringField('название статьи', validators=[DataRequired()])
    content = CKEditorField('контент', validators=[DataRequired()])
    categories = QuerySelectMultipleField('выберете категории',
                                  query_factory=func_categ)
    submit = SubmitField('СОХРАНИТЬ')