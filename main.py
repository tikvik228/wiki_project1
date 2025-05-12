import flask
from flask import Flask, render_template, redirect, url_for, request, send_from_directory, abort, flash, Blueprint
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_restful import Api
from sqlalchemy import desc, func
from flask_admin import Admin
from data import db_session
from data.users import User
from data.pages import Page
from data.categories import Category
from data.history_pages import HistoryPage
from data.uploads_model import Uploads
from sqlite3 import IntegrityError
from data.register import RegisterForm
from data.login_form import LoginForm
from data.page_form import PageForm
from data.user_form import UserForm
from data.category_form import CategForm
from flask_ckeditor import CKEditor, upload_success, upload_fail
from data.flask_admin_views import DashBoardView, AnyPageView, UserModelView, PagesModelView, CategoriesModelView
from data.slug_conventer import IDSlugConverter
from datetime import datetime
import os
from shutil import rmtree
from PIL import Image
from apscheduler.schedulers.background import BackgroundScheduler
from data.uploads_delete_funcs import cleanup_orphaned_uploads, page_file_delete
from api.page_resourses import PageResource, PageListResource

app = Flask(__name__)
scheduler = BackgroundScheduler()
UPLOAD_FOLDER = 'static/image/uploads'
user_profiles_folder = 'static/image/user_profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['SECRET_KEY'] = 'hfim_secret_key'
app.config['CKEDITOR_FILE_UPLOADER'] = 'main.upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.url_map.converters['id_slug'] = IDSlugConverter

api  = Api(app)

ckeditor = CKEditor(app)
login_manager = LoginManager()
login_manager.login_message = 'Авторизуйтесь, чтобы попасть на эту страницу.'
login_manager.init_app(app)
admin = Admin(name='Админ', index_view=DashBoardView(), endpoint='admin')
admin.init_app(app)

main = Blueprint('main', __name__, template_folder='templates')
categories = Blueprint('categories', __name__, template_folder='templates')
pages = Blueprint('pages', __name__, template_folder='templates')
users = Blueprint('users', __name__, template_folder='templates')
def main_func():
    db_session.global_init("db/wiki.db")
    db_sess = db_session.create_session()
    app.register_blueprint(main)
    app.register_blueprint(categories)
    app.register_blueprint(pages)
    app.register_blueprint(users)

    admin.add_view(AnyPageView(name='На Главную'))
    admin.add_view(UserModelView(User, db_sess, name='Пользователи'))
    admin.add_view(PagesModelView(Page, db_sess, name='Страницы'))
    admin.add_view(CategoriesModelView(Category, db_sess, name='Категории'))

    if not scheduler.running:
        scheduler.add_job(
            cleanup_orphaned_uploads,
            'interval',
            args=[app],
            hours=24,
            next_run_time=datetime.now()  # Start immediately first time
        )
        scheduler.start()
    api.add_resource(PageListResource, '/api/pages')
    # для одного объекта
    api.add_resource(PageResource, '/api/pages/<page_id>')
    '''print("gn][rle]rm")
    db_sess = db_session.create_session()
    chel = User(username='prosto_chel', email='perega_sirat')
    chel.set_password('super_secret')
    db_sess.add(chel)
    new_category = Category(name='shitpost')
    db_sess.add(new_category)
    new_page = Page(title='flood_wars', content='<h1>okok</h1><br>not ok ok', last_modified_user_id=1)
    new_page.categories.append(new_category)
    print(new_page.categories, new_category.pages, sep="\n")
    db_sess.add(new_page)
    db_sess.commit()'''
    app.run(debug=True)


@main.route('/')
def home():
    return render_template('index.html', title="Главная")


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

        if os.path.isdir(os.path.join(user_profiles_folder, user.username)):
            path_one = os.path.join(user_profiles_folder, user.username)
            path_two = os.path.join(user_profiles_folder, form.username.data)
            os.rename(path_one, path_two)
        else:
            os.makedirs(os.path.join(user_profiles_folder, form.username.data))

        user.username = form.username.data
        user.email = form.email.data
        user.about = form.about.data
        if form.image_file.data:
            if user.image_file:
                os.remove(os.path.join(user_profiles_folder, user.username, user.image_file))
            img = Image.open(form.image_file.data)
            img.thumbnail((150, 150))
            img.save(os.path.join(user_profiles_folder, user.username, form.image_file.data.filename))
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
    path = os.path.join(user_profiles_folder, user.username)
    if os.path.exists(path):
        rmtree(path)
    db_sess.delete(user)
    db_sess.commit()
    return redirect(url_for('main.home'))


@pages.route('/pages')
def all_pages():
    db_sess = db_session.create_session()
    pages = db_sess.query(Page).order_by(func.lower(Page.title)).all()
    return render_template('all_pages.html', pages=pages)


@pages.route('/pages/<id_slug:id>', methods=['GET', 'POST'])
def show_page(id):
    db_sess = db_session.create_session()
    page = db_sess.query(Page).filter(Page.id == id).first()
    if not page:
        abort(404)
    last_user = db_sess.query(User).filter(page.last_modified_user_id == User.id).first()
    return render_template('page.html', page=page, curr_page=page, user=last_user)

@pages.route('/create_page', methods=['GET', 'POST'])
@login_required
def add_page():
    add_form = PageForm()
    print(add_form.title.label)
    if add_form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Page).filter(Page.title == add_form.title.data).first():
            return render_template('add_page.html', title='Добавление страницы',
                                   form=add_form,
                                   message="Такая страница уже существует")
        category_ids = [c.id for c in add_form.categories.data]
        categories = db_sess.query(Category).filter(Category.id.in_(category_ids)).all()
        page = Page(title=add_form.title.data,
                    content=add_form.content.data,
                    last_modified_user_id=current_user.id)
        page.categories = categories
        old_page = HistoryPage(title=add_form.title.data,
                    content=add_form.content.data,
                    user=current_user)
        old_page.categories = categories
        page.history_versions.append(old_page)
        db_sess.add(page)
        db_sess.add(old_page)
        db_sess.commit()
        print(page.categories)
        return redirect(url_for('pages.show_page', id=page))
    return render_template('add_page.html', title='Добавление страницы', form=add_form)


@pages.route('/pages/<id_slug:id>/edit', methods=['GET', 'POST'])
@login_required
def page_edit(id):
    form = PageForm()
    db_sess = db_session.create_session()
    page = db_sess.query(Page).filter(Page.id == id).first()
    if not page:
        abort(404)
    if request.method == "GET":
        form.title.data = page.title
        form.content.data = page.content
        form.categories.data = page.categories

    if form.validate_on_submit():
        page.title = form.title.data
        page.content = form.content.data
        category_ids = [c.id for c in form.categories.data]
        categories = db_sess.query(Category).filter(Category.id.in_(category_ids)).all()
        page.categories = categories
        page.last_modified_user_id = current_user.id
        page.modified_date = datetime.now()
        old_page = HistoryPage(title=form.title.data,
                                content=form.content.data,
                                user=current_user)
        old_page.categories = categories
        page.history_versions.append(old_page)
        db_sess.add(old_page)
        db_sess.commit()
        return redirect(url_for('pages.show_page', id=page))
    return render_template('add_page.html', title=f'Редактирование {page.title}', form=form)


@pages.route('/pages/<id_slug:id>/delete', methods=['GET', 'POST'])
@login_required
def page_delete(id):
    if current_user.role != 'admin':
        flash('у вас недостаточно прав для этого действия', 'warning')
    else:
        db_sess = db_session.create_session()
        page = db_sess.query(Page).filter(Page.id == id).first()
        if page:
            page_file_delete(app.config['UPLOAD_FOLDER'], id)
            # здесь вызов функции удаления всех картинок
            for old in page.history_versions:
                db_sess.delete(old)
            db_sess.delete(page)
            db_sess.commit()
            flash('Страница была успешно удалена!', 'success')
        else:
            abort(404)
    return redirect(url_for('main.home'))


@pages.route('/pages/<id_slug:id>/history', methods=['GET', 'POST'])
def page_history(id):
    db_sess = db_session.create_session()
    page = db_sess.query(Page).filter(Page.id == id).first()
    if page:
        curr_old_pages = page.history_versions
    else:
        abort(404)
    return render_template('history_of_page.html', title=f'История {page.title}', versions=list(reversed(curr_old_pages)))


@pages.route('/pages/old/<id_slug:old_id>', methods=['GET', 'POST'])
def show_old_page(old_id):
    db_sess = db_session.create_session()
    h_page = db_sess.query(HistoryPage).filter(HistoryPage.id == old_id).first()
    if not h_page:
        abort(404)
    return render_template('page.html', page=h_page, curr_page=h_page.page, old=True,
                            user=h_page.user)


@pages.route('/pages/<id_slug:id>/rollback/<id_slug:old_id>')
@login_required
def rollback_page(id, old_id):
    db_sess = db_session.create_session()
    h_page = db_sess.query(HistoryPage).filter(HistoryPage.id == old_id).first()
    page = db_sess.query(Page).filter(Page.id == id).first()
    if h_page.page == page:
        page.title = h_page.title
        page.content = h_page.content
        page.categories = h_page.categories
        page.last_modified_user_id = h_page.user_id
        page.modified_date = h_page.modified_date
        new_h_page = HistoryPage(title=h_page.title, content=h_page.content,
                                 categories = h_page.categories, user=h_page.user, is_rollback=True,
                                 modified_date=h_page.modified_date)
        page.history_versions.append(new_h_page)
        db_sess.add(new_h_page)
        db_sess.commit()
    else:
        abort(400)
    return redirect(url_for('pages.show_page', id=page))

@categories.route('/categories')
def all_categories():
    db_sess = db_session.create_session()
    categs = db_sess.query(Category).order_by(func.lower(Category.name)).all()
    return render_template('all_categories.html', categs=categs)

@categories.route('/categories/<id_slug:id>')
def show_category(id):
    db_sess = db_session.create_session()
    ctg = db_sess.query(Category).filter(Category.id == id).first()
    return render_template('category.html', category=ctg)

@categories.route('/create_category', methods=['GET', 'POST'])
@login_required
def add_category():
    add_form = CategForm()
    if add_form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(Category).filter(Category.name == add_form.name.data).first():
            return render_template('add_categ.html', title='Добавление категории',
                                   form=add_form,
                                   message="Такая категория уже существует")
        categ = Category(name=add_form.name.data)
        db_sess.add(categ)
        db_sess.commit()
        return redirect(url_for('categories.show_category', id=categ))
    return render_template('add_categ.html', title='Добавление категории', form=add_form)

@categories.route('/categories/<id_slug:id>/edit', methods=['GET', 'POST'])
@login_required
def category_edit(id):
    form = CategForm()
    db_sess = db_session.create_session()
    categ = db_sess.query(Category).filter(Category.id == id).first()
    if not categ:
        abort(404)
    if request.method == "GET":
        form.name.data = categ.name

    if form.validate_on_submit():
        categ.name = form.name.data
        db_sess.commit()
        return redirect(url_for('categories.show_category', id=categ))
    return render_template('add_categ.html', title=f'Редактирование {categ.name}', form=form)


@categories.route('/categories/<id_slug:id>/delete', methods=['GET', 'POST'])
@login_required
def category_delete(id):
    if current_user.role != 'admin':
        flash('у вас недостаточно прав для этого действия', 'warning')
    else:
        db_sess = db_session.create_session()
        categ = db_sess.query(Category).filter(Category.id == id).first()
        if categ:
            db_sess.delete(categ)
            db_sess.commit()
            flash('Категория была успешно удалена!', 'success')
        else:
            abort(404)
    return redirect(url_for('main.home'))


@main.route('/files/<path:filename>')
def uploaded_files(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@main.route('/files')
def all_files():
    db_sess = db_session.create_session()
    files = db_sess.query(Uploads).order_by(desc(Uploads.date)).all()
    return render_template('all_files.html', files=files)


@main.route('/upload', methods=['POST'])
def upload():
    f = request.files.get('upload')
    # Add more validations here
    extension = f.filename.split('.')[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return upload_fail(message='Image only!')
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f.filename)
    f.save(filepath)

    db_sess = db_session.create_session()
    file = Uploads(filename=f.filename, date=datetime.fromtimestamp(os.path.getmtime(filepath)),
                   user=current_user)
    db_sess.add(file)
    db_sess.commit()

    url = url_for('main.uploaded_files', filename=f.filename)
    return upload_success(url)



@app.template_global()
def file_exists(filepath):
    return os.path.exists(filepath)

if __name__ == '__main__':
    main_func()