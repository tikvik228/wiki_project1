import os
from datetime import datetime
from shutil import rmtree
from wiki_app.extensions import login_manager
from PIL import Image
from flask import Blueprint, render_template, current_app, send_from_directory, request, url_for, abort, redirect, flash
from flask_ckeditor import upload_fail, upload_success
from flask_login import current_user, login_required, login_user, logout_user, LoginManager
from sqlalchemy import desc, func

from wiki_app.data import db_session
from wiki_app.data.models.users import User
from wiki_app.data.models.pages import Page
from wiki_app.data.models.categories import Category
from wiki_app.data.models.history_pages import HistoryPage
from wiki_app.data.models.uploads_model import Uploads
from wiki_app.data.forms.register import RegisterForm
from wiki_app.data.forms.login_form import LoginForm
from wiki_app.data.forms.user_form import UserForm
from wiki_app.data.utils.uploads_delete_funcs import cleanup_orphaned_uploads, page_file_delete

users = Blueprint('users', __name__)

@users.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пользователь с такой почтой уже есть")
        if db_sess.query(User).filter(User.username == form.username.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пользователь с таким ником уже есть")
        user = User(
            username=form.username.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        if user.id == 1:
            user.role = 'admin'
        db_sess.commit()
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    try:
        return db_sess.get(User, user_id)
    finally:
        db_sess.close()


@users.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.home'))
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@users.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route('/users/<id_slug(attr="username"):id>')
def show_user(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if not user:
        abort(404)
    return render_template('user_profile.html', user=user)

@users.route('/users/<id_slug(attr="username"):id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if not user:
        abort(404)
    if user.id != current_user.id:
        flash('вы не можете изменять информацию о чужом аккаунте', 'danger')
        return redirect(url_for('main.home'))
    form = UserForm()
    if request.method == "GET":
        form.username.data = user.username
        form.email.data = user.email
        form.about.data = user.about

    if form.validate_on_submit():
        print("Form errors:", form.errors)  # Check validation errors
        print("Files in request:", request.files)
        if db_sess.query(User).filter(User.email == form.email.data, User.id != user.id).first():
            return render_template('user_edit.html', title='Изменение данных пользователя',
                                   form=form,
                                   message="Пользователь с такой почтой уже есть")
        if db_sess.query(User).filter(User.username == form.username.data, User.id != user.id).first():
            return render_template('user_edit.html', title='Изменение данных пользователя',
                                   form=form,
                                   message="Пользователь с таким ником уже есть")

        if os.path.isdir(os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username)):
            path_one = os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username)
            path_two = os.path.join(current_app.config['USER_PROFILES_FOLDER'], form.username.data)
            os.rename(path_one, path_two)
        else:
            os.makedirs(os.path.join(current_app.config['USER_PROFILES_FOLDER'], form.username.data))

        user.username = form.username.data
        user.email = form.email.data
        user.about = form.about.data
        if form.image_file.data:
            if user.image_file:
                os.remove(os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username, user.image_file))
            img = Image.open(form.image_file.data)
            img.thumbnail((150, 150))
            img.save(os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username, form.image_file.data.filename))
            user.image_file = form.image_file.data.filename
        db_sess.commit()
        return redirect(url_for('users.show_user', id=user))
    return render_template('user_edit.html', title='Изменение данных пользователя', form=form)

@users.route('/users/<id_slug(attr="username"):id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if not user:
        abort(404)
    if user.id != current_user.id and current_user.role != 'admin':
        flash('вы не можете удалить этот аккаунт', 'danger')
        return redirect(url_for('main.home'))
    path = os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username)
    if os.path.exists(path):
        rmtree(path)
    db_sess.delete(user)
    db_sess.commit()
    return redirect(url_for('main.home'))