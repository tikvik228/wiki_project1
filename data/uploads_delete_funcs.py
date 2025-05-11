import os
from data import db_session
from data.pages import Page
from data.history_pages import HistoryPage
from data.uploads_model import Uploads
from re import findall
from urllib.parse import unquote
from datetime import datetime, timedelta


def cleanup_orphaned_uploads(app):
    with app.app_context():
        # Same cleanup logic as above
        # Get all files in upload directory
        upload_dir = app.config['UPLOAD_FOLDER']
        all_files = set(os.listdir(upload_dir))

        # Get all files referenced in articles
        db_sess = db_session.create_session()
        used_files = set()
        pages = db_sess.query(Page).all()
        old_pages = db_sess.query(HistoryPage).all()
        for p in pages:
            image_urls = findall(r'src="([^"]+)"', p.content)
            for url in image_urls:
                if url.startswith('/files/'):
                    encoded_filename = url.split('/files/')[-1]
                    decoded_filename = unquote(encoded_filename)
                    used_files.add(decoded_filename)
        for op in old_pages:
            op_image_urls = findall(r'src="([^"]+)"', op.content)
            for url in op_image_urls:
                if url.startswith('/files/'):
                    encoded_filename = url.split('/files/')[-1]
                    decoded_filename = unquote(encoded_filename)
                    used_files.add(decoded_filename)
        # Find orphaned files (older than 1 day to avoid deleting fresh uploads)
        orphaned_files = []
        for filename in (all_files - used_files):
            filepath = os.path.join(upload_dir, filename)
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath))
            if file_age > timedelta(hours=24):
                try:
                    os.remove(filepath)
                    orphaned_files.append(filename)
                except Exception as e:
                    app.logger.error(f"Error deleting {filename}: {e}")


def page_file_delete(app, id):
    db_sess = db_session.create_session()
    page = db_sess.query(Page).filter(Page.id == id).first()
    all_image_urls = set()
    for h_page in page.history_versions:
        all_image_urls.update(findall(r'src="([^"]+)"', h_page.content))
    all_image_urls.update(findall(r'src="([^"]+)"', page.content))

    for url in all_image_urls:
        if url.startswith('/files/'):  # Only delete files from your upload folder
            encoded_filename = url.split('/files/')[-1]
            decoded_filename = unquote(encoded_filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], decoded_filename)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    #file_in_db = db_sess.query(Uploads).
                    app.logger.info(f"Deleted file: {file_path}")
                else:
                    app.logger.warning(f"File not found: {file_path}")
            except Exception as e:
                app.logger.error(f"Error deleting file {file_path}: {e}")