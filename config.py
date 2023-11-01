import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    PAGE_SIZE = 20

    SECRET_KEY = os.environ.get('SECRET_KEY', 'Override this in production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                             'sqlite:///' + os.path.join(basedir, 'app.db')).replace('postgres://', 'postgresql://')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = CELERY_BROKER_URL = CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    ELASTICSEARCH_URL = os.environ.get('ELASTICSEARCH_URL')

    FERNET_KEY = os.environ.get('FERNET_KEY')

    CAS_SERVER = 'https://secure.its.yale.edu'
    CAS_AFTER_LOGIN = 'index'
    CAS_LOGIN_ROUTE = '/cas/login'
    CAS_AFTER_LOGOUT = '/'

    # Email sending with Gmail
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    # Authentication
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    # Recipients for diagnostic emails
    ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS', 'erik.boesen@yale.edu').split(',')
