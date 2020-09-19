from app import app, db
import jwt
import datetime


class User(db.Model):
    __tablename__ = 'users'

    username = db.Column(db.String, primary_key=True)
    registered_on = db.Column(db.Integer)
    last_seen = db.Column(db.Integer)

    def generate_token(self):
        """
        Generate auth token.
        :return: token and expiration timestamp.
        """
        now = datetime.datetime.utcnow()
        payload = {
            'iat': now,
            'exp': now + datetime.timedelta(days=365),
            'sub': self.username,
        }
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        ).decode(), payload['exp']

    @staticmethod
    def from_token(token):
        """
        Decode/validate an auth token.
        :param token: token to decode.
        :return: User whose token this is, or None if token invalid/no user associated
        """
        try:
            payload = jwt.decode(token, app.config.get('SECRET_KEY'))
            """
            is_blacklisted = BlacklistedToken.check_blacklist(token)
            if is_blacklisted:
                # Token was blacklisted following logout
                return None
            """
            return User.query.get(payload['sub'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            # Signature expired, or token otherwise invalid
            return None


class Student(db.Model):
    __tablename__ = 'students'
    _to_expand = ()
    _to_exclude = ()

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    netid = db.Column(db.String)
    upi = db.Column(db.Integer)
    forename = db.Column(db.String, nullable=False)
    surname = db.Column(db.String, nullable=False)
    image_id = db.Column(db.Integer)
    year = db.Column(db.Integer)
    college = db.Column(db.String)
    pronoun = db.Column(db.String)
    email = db.Column(db.String, nullable=False)
    building_code = db.Column(db.String)
    entryway = db.Column(db.String)
    floor = db.Column(db.Integer)
    suite = db.Column(db.Integer)
    room = db.Column(db.String)
    birthday = db.Column(db.String)
    major = db.Column(db.String)
    address = db.Column(db.String)
    state = db.Column(db.String)
    leave = db.Column(db.Boolean, default=False)

    @staticmethod
    def search(filters):
        students_query = Student.query
        if filters:
            for category in filters:
                if category not in ('college', 'year', 'major', 'building_code',
                                    'entryway', 'floor', 'suite', 'room', 'state', 'leave'):
                    return None
                if not isinstance(filters[category], list):
                    return None
                students_query = students_query.filter(getattr(Student, category).in_(filters[category]))
        students = students_query.all()
        return students
