from flask import Flask, url_for, redirect, flash
from flask_admin import Admin, expose, AdminIndexView, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.model import BaseModelView
from flask_login import login_required, current_user
from wtforms.validators import DataRequired
from wtforms import StringField, TextAreaField, SelectField, IntegerField
from flask_wtf import FlaskForm

from data.db_session import create_session


class DashBoardView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('users.login'))
        else:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))
    @login_required
    @expose('/')
    def admin_panel(self):

        return self.render('index_admin.html', username=current_user.username)


class AnyPageView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('users.login'))
        else:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))
    @login_required
    @expose('/')
    def any_page(self):
        return redirect(url_for('main.home'))


class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('users.login'))
        else:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))

class UserModelView(MyModelView):
    can_create = False
    can_delete = False
    column_list = ('id', 'username', 'email', 'about', 'role', 'created_date')
    form_excluded_columns = ['hashed_password', 'files', 'edits']
    column_searchable_list = ['username', 'email']
    form_widget_args = {
        'id': {
            'readonly': True

        },
        'username': {
            'readonly': True
                },
        'email': {
            'readonly': True
        },
        'about': {
            'readonly': True
        },
        'created_date': {
            'readonly': True
        },
        'image_file': {
            'readonly': True
        }
    }
    form_choices = {'role': [('admin', 'admin'), ('user', 'user')]}


class PagesModelView(MyModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_list = ('id', 'title', 'last_modified_user_id', 'modified_date', 'categories')
    column_searchable_list = ['title', 'modified_date']


class CategoriesModelView(MyModelView):
    column_searchable_list = ['name']
    form_excluded_columns = ['pages', 'history_pages']