from flask import jsonify, g
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import inspect

import json
import datetime
from functools import wraps
import string


def requires_login(f):
    @wraps(f)
    def wrapper_requires_login(*args, **kwargs):
        if g.user is None:
            return fail('Missing or invalid authorization.', code=401)
        return f(*args, **kwargs)
    return wrapper_requires_login


def forbidden_via_api(f):
    @wraps(f)
    def wrapper_forbidden_via_api(*args, **kwargs):
        if g.method_used == 'header':
            return fail('This endpoint is not accessible via the API.', 403)
        return f(*args, **kwargs)
    return wrapper_forbidden_via_api

def succ(message, code=200):
    return (
        jsonify({
            'status': 'success',
            'message': message,
        }),
        code
    )


def fail(message, code=400):
    return (
        jsonify({
            'status': 'fail',
            'message': message,
        }),
        code
    )


class ModelEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # go through each field in this SQLalchemy class
            fields = {}
            for field in obj.__class__.__serializable__:
                val = obj.__getattribute__(field)

                # is this field another SQLalchemy object, or a list of SQLalchemy objects, or a function?
                if isinstance(val.__class__, DeclarativeMeta) or (isinstance(val, list) and len(val) > 0 and isinstance(val[0].__class__, DeclarativeMeta)) or callable(val):
                    # unless we're expanding this field, stop here
                    if field not in obj.__class__._to_expand:
                        # not expanding this field: set it to None and continue
                        fields[field] = None
                        continue

                fields[field] = val

            # Also add any fields that are in PERSISTENT_FIELDS.
            # TODO: Maybe a better way to do this that isn't hard coded?
            for field in PERSISTENT_FIELDS:
                if hasattr(obj, field):
                    fields[field] = obj.__getattribute__(field)

            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


def to_json(model):
    return json.dumps(model, cls=ModelEncoder)

def get_now():
    return int(datetime.datetime.utcnow().timestamp())

PERSISTENT_FIELDS = [
    'socials_instagram',
    'socials_snapchat',
    'privacy_hide_image',
    'privacy_hide_email',
    'privacy_hide_room',
    'privacy_hide_phone',
    'privacy_hide_address',
    'privacy_hide_major',
    'privacy_hide_birthday'
]

def scrub_hidden_data(person):
    if hasattr(person, "privacy_hide_image") and getattr(person, "privacy_hide_image"):
        setattr(person, "image", None)
    if hasattr(person, "privacy_hide_email") and getattr(person, "privacy_hide_email"):
        setattr(person, "email", None)
    if hasattr(person, "privacy_hide_room") and getattr(person, "privacy_hide_room"):
        setattr(person, "entryway", None)
        setattr(person, "floor", None)
        setattr(person, "suite", None)
        setattr(person, "room", None)
    if hasattr(person, "privacy_hide_phone") and getattr(person, "privacy_hide_phone"):
        setattr(person, "phone", None)
    if hasattr(person, "privacy_hide_address") and getattr(person, "privacy_hide_address"):
        setattr(person, "address", None)
    if hasattr(person, "privacy_hide_major") and getattr(person, "privacy_hide_major"):
        setattr(person, "major", None)
    if hasattr(person, "privacy_hide_birthday") and getattr(person, "privacy_hide_birthday"):
        setattr(person, "birthday", None)
        setattr(person, "birth_month", None)
        setattr(person, "birth_day", None)
    return person

INSTAGRAM_ALLOWED_CHARSET = set(string.ascii_letters + string.digits + '._')
def is_valid_instagram_username(username):
    return (
        all(c in INSTAGRAM_ALLOWED_CHARSET for c in username) and
        len(username) >= 1 and len(username) <= 30
    )

SNAPCHAT_ALLOWED_CHARSET = set(string.ascii_letters + string.digits + '._-')
def is_valid_snapchat_username(username):
    return (
        all(c in SNAPCHAT_ALLOWED_CHARSET for c in username) and
        len(username) >= 3 and len(username) <= 15
    )
