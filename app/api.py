from flask import Blueprint, jsonify, request, g, abort
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
        print('User: ' + g.user.username)


@api_bp.route('/students', methods=['POST'])
def api_students():
    criteria = request.get_json() or {}
    criteria.update({'school_code': 'YC'})
    students = Person.search(criteria)
    return to_json(students)


@api_bp.route('/people', methods=['POST'])
def api_people():
    criteria = request.get_json() or {}
    people = Person.search(criteria)
    return to_json(people)
