from data import db_session
from flask import jsonify
from flask_restful import Resource, abort
from werkzeug.security import generate_password_hash
from data.pages import Page
from data.users import User
from data.categories import Category
from data.history_pages import HistoryPage
from api.page_reqparse import page_parser
from datetime import datetime
from data.uploads_delete_funcs import page_file_delete

upload_dir = 'static/image/uploads'

def abort_if_page_not_found(page_id):
    session = db_session.create_session()
    page = session.query(Page).get(page_id)
    if not page:
        abort(404, message=f"работа с id {page_id} не найдена")

def abort_if_page_id_not_int(page_id):
    try:
        page_id = int(page_id)
    except ValueError:
        abort(404, message=f"id страницы должен быть числом")

class MyResource(Resource):
    '''родительский класс для обоих классов работы с общими методами'''
    def _serialize_page(self, page):
            return {
                'id': page.id,
                'title': page.title,
                'content': page.content,
                'modified_date': page.modified_date.isoformat(),
                'last_modified_user_id': page.last_modified_user_id,
                'categories': [{'id': c.id, 'name': c.name} for c in page.categories],
                'history_count': len(page.history_versions)
        }

    def _create_history_version(self, page, user_id, categories, sess):
        """"""
        history = HistoryPage(
            title=page.title,
            content=page.content,
            modified_date=datetime.now(),
            is_rollback=False,
            user_id=user_id,
            page_id=page.id,
        )
        history.categories= categories
        page.history_versions.append(history)
        sess.add(history)
        return history


class PageResource(MyResource):
    '''класс для операций с одной работой'''
    def get(self, page_id):
        abort_if_page_id_not_int(page_id)
        abort_if_page_not_found(page_id)
        db_sess = db_session.create_session()
        page = db_sess.query(Page).get(page_id)
        return jsonify({'page': self._serialize_page(page)})

    def put(self, page_id):
        abort_if_page_id_not_int(page_id)
        abort_if_page_not_found(page_id)
        args = page_parser.parse_args()
        db_sess = db_session.create_session()
        page = db_sess.query(Page).get(page_id)
        if db_sess.query(Page).filter(Page.title == args.title,
                                        Page.id != page_id).first():
            abort(409, message="Такой заголовок уже есть")
        user = db_sess.query(User).get(args.user_id)
        if not user:
            abort(404, message="пользователь с таким id не найден")
        page.title = args.title
        page.content = args.content
        page.last_modified_user_id = args.user_id
        page.modified_date = datetime.now()

        print("ok")
        if args.category_id is not None:
            categories = db_sess.query(Category).filter(Category.id.in_(args.category_id)).all()
            page.categories = categories

        self._create_history_version(
            page=page,
            user_id=args.user_id,
            categories=page.categories,
            sess = db_sess
        )
        db_sess.commit()
        return jsonify({'success': 'OK'})

    def delete(self, page_id):
        abort_if_page_id_not_int(page_id)
        abort_if_page_not_found(page_id)
        db_sess = db_session.create_session()
        page = db_sess.query(Page).get(page_id)
        page_file_delete(upload_dir, page_id)
        for old in page.history_versions:
            db_sess.delete(old)
        db_sess.delete(page)
        db_sess.commit()
        return jsonify({'success': 'OK'})



class PageListResource(MyResource):
    def get(self):
        db_sess = db_session.create_session()
        page_list = db_sess.query(Page).all()
        return jsonify({'pages': [self._serialize_page(i)
                                 for i in page_list]})

    def post(self):
        """Create new page with initial history version"""
        args = page_parser.parse_args()
        db_sess = db_session.create_session()

        # Validate unique title
        if db_sess.query(Page).filter(Page.title == args.title).first():
            abort(409, message="Такое название стрницы уже есть")


        page = Page(
            title=args.title,
            content=args.content,
            last_modified_user_id=args.user_id,
            modified_date=datetime.now()
        )

        # Handle categories
        if args.category_ids:
            categories = db_sess.query(Category).filter(Category.id.in_(args.category_ids)).all()
            page.categories = categories

        db_sess.add(page)
        db_sess.flush()  # Get page ID before creating history

        # Create initial history version
        self._create_history_version(
            page=page,
            user_id=args.user_id,
            categories=categories if args.category_ids else [],
            sess = db_sess
        )

        db_sess.commit()
        return jsonify({'id': page.id})