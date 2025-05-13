from flask import Blueprint, render_template, request, url_for, abort, redirect, flash
from flask_login import current_user, login_required
from sqlalchemy import func

from wiki_app.data import db_session
from wiki_app.data.models.categories import Category
from wiki_app.data.forms.category_form import CategForm


categories = Blueprint('categories', __name__, )

@categories.route('/categories')
def all_categories():
    '''все категории'''
    db_sess = db_session.create_session()
    categs = db_sess.query(Category).order_by(func.lower(Category.name)).all()
    return render_template('all_categories.html', categs=categs)

@categories.route('/categories/<id_slug(attr="name"):id>')
def show_category(id):
    '''конкретная категория'''
    db_sess = db_session.create_session()
    ctg = db_sess.query(Category).filter(Category.id == id).first()
    return render_template('category.html', category=ctg)

@categories.route('/create_category', methods=['GET', 'POST'])
@login_required
def add_category():
    '''создать категорию'''
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

@categories.route('/categories/<id_slug(attr="name"):id>/edit', methods=['GET', 'POST'])
@login_required
def category_edit(id):
    '''изменение категории'''
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


@categories.route('/categories/<id_slug(attr="name"):id>/delete', methods=['GET', 'POST'])
@login_required
def category_delete(id):
    '''удаление категории'''
    if current_user.role != 'admin': # удалять категории можно только админам
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