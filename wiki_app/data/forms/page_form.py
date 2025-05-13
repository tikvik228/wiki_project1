from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditorField
from wiki_app.data.db_session import create_session
from wiki_app.data.models.categories import Category

def func_categ():
    db_sess = create_session()
    try:
        return db_sess.query(Category).all()
    finally:
        db_sess.close()

class PageForm(FlaskForm):
    '''поле категорий показывает полученные из бд категории'''
    title = StringField('название статьи', validators=[DataRequired()])
    content = CKEditorField('контент', validators=[DataRequired()])
    categories = QuerySelectMultipleField('выберете категории',
                                  query_factory=func_categ, validators=[DataRequired()])
    submit = SubmitField('СОХРАНИТЬ')