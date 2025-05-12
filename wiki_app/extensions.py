from flask_restful import Api
from flask_ckeditor import CKEditor
from flask_login import LoginManager
from flask_admin import Admin
from wiki_app.config import Config
from wiki_app.data.admin.flask_admin_views import DashBoardView
import os
from flask import current_app

ckeditor = CKEditor()
login_manager = LoginManager()
login_manager.login_message = 'Авторизуйтесь, чтобы попасть на эту страницу.'

admin = Admin(name='Админ', index_view=DashBoardView(), endpoint='admin')
api = Api()


def register_template_globals(app):
    @app.template_global()
    def file_exists(filepath):
        if not os.path.isabs(filepath):
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filepath)
        return os.path.exists(filepath)