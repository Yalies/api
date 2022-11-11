from flask import Flask
from config import Config
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cas import CAS
from flask_redis import FlaskRedis

from elasticsearch import Elasticsearch
import logging


app = Flask(__name__)
app.config.from_object(Config)
cors = CORS(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
cas = CAS(app)
redis = FlaskRedis(app)
elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
    if app.config['ELASTICSEARCH_URL'] else None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from app import routes, errors, api
app.register_blueprint(api.api_bp, url_prefix='/api')
