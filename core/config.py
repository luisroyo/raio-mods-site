import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '../.env'))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}