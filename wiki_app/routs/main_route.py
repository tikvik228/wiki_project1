import os
from datetime import datetime

from flask import Blueprint, render_template, current_app, send_from_directory, request, url_for
from flask_ckeditor import upload_fail, upload_success
from flask_login import current_user
from sqlalchemy import desc

from wiki_app.data import db_session
from wiki_app.data.models.users import User
from wiki_app.data.models.pages import Page
from wiki_app.data.models.categories import Category
from wiki_app.data.models.history_pages import HistoryPage
from wiki_app.data.models.uploads_model import Uploads

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('index.html', title="Главная")

@main.route('/files/<path:filename>')
def uploaded_files(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

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
    if extension not in current_app.config['ALLOWED_EXTENSIONS']:
        return upload_fail(message='Image only!')
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f.filename)
    f.save(filepath)

    db_sess = db_session.create_session()
    file = Uploads(filename=f.filename, date=datetime.fromtimestamp(os.path.getmtime(filepath)),
                   user=current_user)
    db_sess.add(file)
    db_sess.commit()

    url = url_for('main.uploaded_files', filename=f.filename)
    return upload_success(url)