from wiki_app.data import db_session
from wiki_app.data.models.pages import Page
from wiki_app.data.models.history_pages import HistoryPage
from re import findall
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime, timedelta
import os


def cleanup_orphaned_uploads(upload_folder_path):
    folder = Path(upload_folder_path) if isinstance(upload_folder_path, str) else upload_folder_path
    all_files = set(os.listdir(folder))


    db_sess = db_session.create_session()
    used_files = set() # общее множество для файлов из страницы и ее версий
    pages = db_sess.query(Page).all()
    old_pages = db_sess.query(HistoryPage).all()
    for p in pages:
        image_urls = findall(r'src="([^"]+)"', p.content) # нахождение всех ссылок в контенте страницы
        for url in image_urls:
            if url.startswith('/files/'): # если ссылка - файл
                encoded_filename = url.split('/files/')[-1] # имя файла в поле закодировано
                decoded_filename = unquote(encoded_filename) # декодирование имени файла
                used_files.add(decoded_filename)
    for op in old_pages: # то же самое с версиями
        op_image_urls = findall(r'src="([^"]+)"', op.content)
        for url in op_image_urls:
            if url.startswith('/files/'):
                encoded_filename = url.split('/files/')[-1]
                decoded_filename = unquote(encoded_filename)
                used_files.add(decoded_filename)

    orphaned_files = [] # брошенные файлы
    # (могут остаться, если пользователь начал редактировать страницу, загрузил изображение,
    # а потом не сохранил страницу)
    for filename in (all_files - used_files):
        filepath = os.path.join(folder, filename)
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(filepath))
        if file_age > timedelta(hours=24): # если файлу больше суток
            try:
                os.remove(filepath)
                orphaned_files.append(filename)
            except Exception as e:
                print(f"Error deleting {filename}: {e}")


def page_file_delete(upload_folder, id):
    '''удаление файлов, принадлежищих странице и версиям при ее удалении'''
    db_sess = db_session.create_session()
    page = db_sess.query(Page).filter(Page.id == id).first()
    all_image_urls = set()
    for h_page in page.history_versions:
        all_image_urls.update(findall(r'src="([^"]+)"', h_page.content))
    all_image_urls.update(findall(r'src="([^"]+)"', page.content))

    for url in all_image_urls:
        if url.startswith('/files/'):
            encoded_filename = url.split('/files/')[-1]
            decoded_filename = unquote(encoded_filename)
            file_path = os.path.join(upload_folder, decoded_filename)
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                else:
                    print(f"File not found: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")