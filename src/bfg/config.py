import os
import time
import logging

# Run as first thing to setup environment variables
from pathlib import Path
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
env_path = Path(basedir) / '.env'
load_dotenv(verbose=True, dotenv_path=env_path)


class Config:
    USER = os.environ.get('BETFAIRUSER') or None

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BETFAIR_USER = os.environ.get('BETFAIR_USERNAME') or ''
    BETFAIR_PASSWORD = os.environ.get('BETFAIR_PASSWORD') or ''

    # TODO can i force subclasses to have a __call__ impl?
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    LOG_LEVEL = logging.INFO
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///bfg.db?check_same_thread=False'
    BETFAIR_APP_KEY = os.environ.get('BETFAIR_APP_KEY_DELAY') or ''


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    SOME_PROPERTY = 'Hej'
    BETFAIR_APP_KEY = os.environ.get('BETFAIR_APP_KEY_PROD') or ''


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
