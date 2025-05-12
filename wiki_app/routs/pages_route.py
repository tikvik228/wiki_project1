import os
from datetime import datetime

from flask import Blueprint, render_template, current_app, send_from_directory, request, url_for, abort, redirect, flash
from flask_ckeditor import upload_fail, upload_success
from flask_login import current_user, login_required
from sqlalchemy import desc, func

from wiki_app.data import db_session
from wiki_app.data.models.users import User
from wiki_app.data.models.pages import Page
from wiki_app.data.models.categories import Category
from wiki_app.data.models.history_pages import HistoryPage
from wiki_app.data.models.uploads_model import Uploads
from wiki_app.data.forms.page_form import PageForm
from wiki_app.data.utils.uploads_delete_funcs import cleanup_orphaned_uploads, page_file_delete

pages = Blueprint('pages', __name__)

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
            page_file_delete(current_app.config['UPLOAD_FOLDER'], id)
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