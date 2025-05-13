import os
from shutil import rmtree
from wiki_app.extensions import login_manager
from PIL import Image
from flask import Blueprint, render_template, current_app, request, url_for, abort, redirect, flash
from flask_login import current_user, login_required, login_user, logout_user

from wiki_app.data import db_session
from wiki_app.data.models.users import User
from wiki_app.data.forms.register import RegisterForm
from wiki_app.data.forms.login_form import LoginForm
from wiki_app.data.forms.user_form import UserForm

users = Blueprint('users', __name__)

@users.route('/register', methods=['GET', 'POST'])
def register():
    '''регистрация пользователя'''
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
        # создание нового юзера если все проверки пройдены
        user = User(
            username=form.username.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        if user.id == 1: # первый зарегистрировавшийся юзер всегда админ
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
    '''авторизация пользователя'''
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


@users.route('/users/<id_slug(attr="username"):id>') # передаем конвентеру нужное человекочитаемое поле
def show_user(id):
    '''показ профиля юзера'''
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if not user:
        abort(404)
    return render_template('user_profile.html', user=user)

@users.route('/users/<id_slug(attr="username"):id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    '''изменение данных юзера'''
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
        # если такая почта или юзернейм уже существуют, но у других пользователей
        if db_sess.query(User).filter(User.email == form.email.data, User.id != user.id).first():
            return render_template('user_edit.html', title='Изменение данных пользователя',
                                   form=form,
                                   message="Пользователь с такой почтой уже есть")
        if db_sess.query(User).filter(User.username == form.username.data, User.id != user.id).first():
            return render_template('user_edit.html', title='Изменение данных пользователя',
                                   form=form,
                                   message="Пользователь с таким ником уже есть")
        # если директория, хранящая аватарку пользователя, уже существует, то переименовать
        # ее в соответствии с новым ником, иначе создать такую
        if os.path.isdir(os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username)):
            path_one = os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username)
            path_two = os.path.join(current_app.config['USER_PROFILES_FOLDER'], form.username.data)
            os.rename(path_one, path_two)
        else:
            os.makedirs(os.path.join(current_app.config['USER_PROFILES_FOLDER'], form.username.data))

        user.username = form.username.data
        user.email = form.email.data
        user.about = form.about.data
        if form.image_file.data: # если был передан файл
            if user.image_file: # изначально поле пустое, если же нет, значит существует файл с прошлой картинкой и мы можем удалить его
                os.remove(os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username, user.image_file))
            img = Image.open(form.image_file.data)
            img.thumbnail((150, 150)) # уменьшение и обрезка изображения для аватара
            # сохранение static/image/user/profiles/<имя юзера>/<имя файла>
            img.save(os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username, form.image_file.data.filename))
            user.image_file = form.image_file.data.filename
        db_sess.commit()
        return redirect(url_for('users.show_user', id=user))
    return render_template('user_edit.html', title='Изменение данных пользователя', form=form)

@users.route('/users/<id_slug(attr="username"):id>/delete', methods=['GET', 'POST'])
@login_required
def delete_user(id):
    '''удаление юзера'''
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id == id).first()
    if not user:
        abort(404)
    if user.id != current_user.id and current_user.role != 'admin': # удалить аккаунт может только сам юзер или админ
        flash('вы не можете удалить этот аккаунт', 'danger')
        return redirect(url_for('main.home'))
    path = os.path.join(current_app.config['USER_PROFILES_FOLDER'], user.username)
    if os.path.exists(path): # если папка с аватаркой юзера существует, удалить и папку, и содержимое
        rmtree(path)
    db_sess.delete(user)
    db_sess.commit()
    return redirect(url_for('main.home'))