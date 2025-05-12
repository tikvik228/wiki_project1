import os
from datetime import datetime
from shutil import rmtree

from PIL import Image
from flask import Blueprint, render_template, current_app, send_from_directory, request, url_for, abort, redirect, flash
from flask_ckeditor import upload_fail, upload_success
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import desc, func

from main import login_manager
from wiki_app.data import db_session
from wiki_app.data.models.users import User
from wiki_app.data.models.pages import Page
from wiki_app.data.models.categories import Category
from wiki_app.data.models.history_pages import HistoryPage
from wiki_app.data.models.uploads_model import Uploads
from wiki_app.data.forms.category_form import CategForm
from wiki_app.data.forms.login_form import LoginForm
from wiki_app.data.forms.user_form import UserForm


categories = Blueprint('categories', __name__, )

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