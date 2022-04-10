from flask import Blueprint, jsonify, request, g, abort
from sqlalchemy import distinct
import time
from app import db, cas
from app.util import to_json, fail, succ
from app.models import User, Person


api_bp = Blueprint('api', __name__)


@api_bp.errorhandler(404)
def not_found(error):
    return fail('Not found.', 404)


@api_bp.errorhandler(401)
def unauthorized(error):
    return fail('You\'re not authorized to perform this action.', 401)


@api_bp.errorhandler(403)
def forbidden(error):
    return fail('You don\'t have permission to do this.', 403)


@api_bp.errorhandler(500)
def internal(error):
    return fail('Internal server error.', 500)


@api_bp.before_request
def check_token():
    if request.method != 'OPTIONS':
        if cas.username:
            g.user = User.query.get(cas.username)
        else:
            token = request.headers.get('Authorization')
            if not token:
                return fail('No token provided.')
            token = token.split(' ')[-1]
            g.user = User.from_token(token)
            if g.user is None:
                return fail('Invalid token.', code=401)
        g.user.last_seen = int(time.time())
        db.session.commit()
        print('User: ' + g.user.id)


@api_bp.route('/filters')
def api_filters():
    filters = {}
    for category in Person.__filterable__:
        filters[category] = untuple(db.session.query(distinct(getattr(Person, category))).order_by(getattr(Person, category)))
    return to_json(filters)


@api_bp.route('/students', methods=['POST'])
def api_students():
    try:
        criteria = request.get_json(force=True) or {}
    except:
        criteria = {}
    if not criteria.get('filters'):
        criteria['filters'] = {}
    if not criteria['filters'].get('school_code'):
        criteria['filters']['school_code'] = []
    criteria['filters']['school_code'].append('YC')
    students = Person.search(criteria)
    return to_json(students)


@api_bp.route('/people', methods=['POST'])
def api_people():
    try:
        criteria = request.get_json(force=True) or {}
    except:
        criteria = {}
    people = Person.search(criteria)
    return to_json(people)


def untuple(tuples):
    return [t[0] for t in tuples]
