from flask_restful import Api
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_admin import Admin
from wiki_app.data.admin.flask_admin_views import DashBoardView
from wiki_app.data import db_session
from wiki_app.data.models.categories import Category

import os
from flask import current_app

ckeditor = CKEditor()
login_manager = LoginManager()
login_manager.login_message = 'Авторизуйтесь, чтобы попасть на эту страницу.'

admin = Admin(name='Админ', index_view=DashBoardView(), endpoint='admin')
api = Api()

def register_template_globals(app):
    ''' функция, которая нужна в all_files.html чтобы проверить, существует ли изображение'''
    @app.template_global()
    def file_exists(filepath):
        if not os.path.isabs(filepath):
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filepath)
        return os.path.exists(filepath)

    @app.template_global()
    def get_category(category_name):
        '''функция, нужная в навигационной панели для отображения страниц категории в раскрывающемся списке'''
        db_sess = db_session.create_session()
        categ = db_sess.query(Category).filter(Category.name.ilike(category_name)).first()
        if categ: return categ

