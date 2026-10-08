import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'foodwise.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ML model directory
    ML_MODEL_DIR = os.path.join(basedir, 'ml', 'models')

    # AI / LLM
    AI_PROVIDER = os.environ.get('AI_PROVIDER', '').lower()
    AI_API_KEY = os.environ.get('AI_API_KEY', '')
    WATSONX_URL = os.environ.get('WATSONX_URL', '')
    WATSONX_PROJECT_ID = os.environ.get('WATSONX_PROJECT_ID', '')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
