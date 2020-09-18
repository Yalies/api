from flask import Blueprint, jsonify, request, g
import time
from app import db
from app.util import to_json, fail, succ
from app.models import User, Student


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
        token = request.headers.get('Authorization')
        if not token:
            return fail('No token provided.')
        token = token.split(' ')[-1]
        g.me = User.from_token(token)
        if g.me is None:
            abort(401)
        g.me.last_seen = int(time.time())
        db.session.commit()
        print('User: ' + g.me.username)
        g.json = request.get_json()


@api_bp.route('/students')
def api_students(slug):
    students = Student.query.all()
    return to_json(students)
