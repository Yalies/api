from flask import Blueprint, jsonify, request, g, abort
from sqlalchemy import distinct
import time
from app import db, cas
from app.util import to_json, fail, succ, requires_login
from app.models import User, Person, Group, PersonPersistent


api_bp = Blueprint('api', __name__)


@api_bp.errorhandler(404)
def not_found(error):
    return fail('Not found.', 404)


@api_bp.errorhandler(401)
def unauthorized(error):
    return fail('Missing or invalid Authorization header. Please consult https://yalies.io/apidocs to obtain an API key.', 401)


@api_bp.errorhandler(403)
def forbidden(error):
    return fail('You don\'t have permission to do this.', 403)


@api_bp.errorhandler(500)
def internal(error):
    return fail('Internal server error.', 500)


@api_bp.route('/filters')
@requires_login
def api_filters():
    filters = {}
    for category in Person.__filterable__:
        filters[category] = untuple(db.session.query(distinct(getattr(Person, category))).order_by(getattr(Person, category)))
    return to_json(filters)


@api_bp.route('/students', methods=['POST'])
@requires_login
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
@requires_login
def api_people():
    try:
        criteria = request.get_json(force=True) or {}
    except:
        criteria = {}
    people = Person.search(criteria)
    return to_json(people)


@api_bp.route('/groups', methods=['POST'])
@requires_login
def api_groups():
    try:
        criteria = request.get_json(force=True) or {}
    except:
        criteria = {}
    groups = Group.search(criteria)
    return to_json(groups)


def untuple(tuples):
    return [t[0] for t in tuples]
