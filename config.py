import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'Override this in production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                             'sqlite:///' + os.path.join(basedir, 'app.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CELERY_BROKER_URL = CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    CAS_SERVER = 'https://secure.its.yale.edu'
    CAS_AFTER_LOGIN = 'index'
    CAS_LOGIN_ROUTE = '/cas/login'
    CAS_AFTER_LOGOUT = 'index'

    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
    S3_SECRET_ACCESS_KEY = os.environ.get('S3_SECRET_ACCESS_KEY')
    S3_LOCATION = 'https://' + S3_BUCKET + '.s3.amazonaws.com/'
