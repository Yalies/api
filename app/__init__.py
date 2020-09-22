from flask import Flask
from config import Config
from celery import Celery
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_whooshee import Whooshee
from flask_migrate import Migrate
from flask_cas import CAS


app = Flask(__name__)
app.config.from_object(Config)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
cors = CORS(app)
db = SQLAlchemy(app)
whooshee = Whooshee(app)
whooshee.reindex()
migrate = Migrate(app, db)
cas = CAS(app)

from app import routes, errors, api
app.register_blueprint(api.api_bp, url_prefix='/api')
