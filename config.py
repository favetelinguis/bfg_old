import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:

    USER = os.environ.get('BETFAIRUSER') or None # TODO do i need None here what if no env is set?

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    SOME_PROPERTY = 'Hej'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
