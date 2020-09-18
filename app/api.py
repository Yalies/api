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


@api_bp.before_request
def check_token():
    if request.method != 'OPTIONS':
        token = request.headers.get('Authorization')
        token = token.split(' ')[-1]
        g.me = User.from_token(token)
        if g.me is None:
            abort(401)
        g.me.last_seen = datetime.datetime.utcnow()
        db.session.commit()
        print('User: ' + g.me.name)
        g.json = request.get_json()


@api_bp.route('/students')
def api_students(slug):


@api_bp.route('/bot/<slug>/instance/<group_id>')
def api_instance(slug, group_id):
    token = request.args.get("token")
    g.bot = Bot.query.filter_by(slug=slug).first_or_404()
    if not token or token != g.bot.token:
        return {"error": "Missing or invalid token."}, 401
    instance = Instance.query.filter_by(bot_id=g.bot.id, group_id=group_id).first_or_404()
    json = {"id": instance.id}
    if g.bot.has_user_token_access:
        json["token"] = User.query.get(instance.owner_id).token
    return jsonify(json)
