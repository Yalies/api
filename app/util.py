from flask import jsonify
from sqlalchemy.ext.declarative import DeclarativeMeta

import json
import datetime


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
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


def to_json(model):
    return json.dumps(model, cls=ModelEncoder)

def get_now():
    return int(datetime.datetime.utcnow().timestamp())
