from flask import Flask
from wiki_app.config import Config
from wiki_app.extensions import ckeditor, login_manager, admin, api, register_template_globals
from wiki_app.data import db_session
from wiki_app.routs.main_route import main
from wiki_app.routs.users_route import users
from wiki_app.routs.pages_route import pages
from wiki_app.routs.categories_route import categories
from wiki_app.data.utils.slug_conventer import IDSlugConverter
from wiki_app.data.admin.flask_admin_views import DashBoardView, AnyPageView, UserModelView, PagesModelView, CategoriesModelView
from wiki_app.data.models.users import User
from wiki_app.data.models.pages import Page
from wiki_app.data.models.categories import Category
from wiki_app.api.page_resourses import PageResource, PageListResource
from apscheduler.schedulers.background import BackgroundScheduler
from wiki_app.data.utils.uploads_delete_funcs import cleanup_orphaned_uploads
from wiki_app.data.models.history_pages import HistoryPage
from wiki_app.data.models.uploads_model import Uploads
from datetime import datetime

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    scheduler = BackgroundScheduler()

    # Initialize extensions
    ckeditor.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)
    db_session.global_init("wiki_app/db/wiki.db")
    db_sess = db_session.create_session()
    app.url_map.converters['id_slug'] = IDSlugConverter

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(pages)
    app.register_blueprint(categories)


    # Admin views
    admin.add_view(AnyPageView(name='На Главную'))
    admin.add_view(UserModelView(User, db_sess, name='Пользователи'))
    admin.add_view(PagesModelView(Page, db_sess, name='Страницы'))
    admin.add_view(CategoriesModelView(Category, db_sess, name='Категории'))

    if not scheduler.running:
        scheduler.add_job(
            cleanup_orphaned_uploads,
            'interval',
            args=[str(Config.UPLOAD_FOLDER)],
            hours=24,
            next_run_time=datetime.now()  # Start immediately first time
        )
        scheduler.start()

    api.add_resource(PageListResource, '/api/pages')
    api.add_resource(PageResource, '/api/pages/<page_id>')

    register_template_globals(app)

    return app