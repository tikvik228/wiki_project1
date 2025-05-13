from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Config:
    SECRET_KEY = 'hfim_secret_key'
    UPLOAD_FOLDER = BASE_DIR / 'wiki_app' / 'static' / 'image' / 'uploads'
    USER_PROFILES_FOLDER = BASE_DIR / 'wiki_app' / 'static' / 'image' / 'user_profiles'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'} # возможные расширения загруженных файлов
    CKEDITOR_FILE_UPLOADER = 'main.upload' # функция, отвечающая за сохранение загруженных в ckeditor файлов