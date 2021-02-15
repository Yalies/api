from app import app, db
from app.search import SearchableMixin
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
        ), payload['exp']

    @staticmethod
    def from_token(token):
        """
        Decode/validate an auth token.
        :param token: token to decode.
        :return: User whose token this is, or None if token invalid/no user associated
        """
        try:
            payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=['HS256'])
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


class Person(SearchableMixin, db.Model):
    __tablename__ = 'person'
    __searchable__ = ['first_name', 'last_name', 'netid', 'college', 'email', 'residence', 'major', 'address']
    _to_exclude = ('id')

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    netid = db.Column(db.String)
    upi = db.Column(db.Integer)

    title = db.Column(db.String)
    first_name = db.Column(db.String, nullable=False)
    nickname = db.Column(db.String)
    middle_name = db.Column(db.String)
    last_name = db.Column(db.String, nullable=False)
    suffix = db.Column(db.String)
    pronoun = db.Column(db.String)

    image_id = db.Column(db.Integer)
    image = db.Column(db.String)
    year = db.Column(db.Integer)
    college = db.Column(db.String)
    email = db.Column(db.String)
    residence = db.Column(db.String)
    building_code = db.Column(db.String)
    entryway = db.Column(db.String)
    floor = db.Column(db.Integer)
    suite = db.Column(db.Integer)
    room = db.Column(db.String)
    birthday = db.Column(db.String)
    major = db.Column(db.String)
    address = db.Column(db.String)
    phone = db.Column(db.String)
    access_code = db.Column(db.String)
    leave = db.Column(db.Boolean, default=False)
    eli_whitney = db.Column(db.Boolean, default=False)

    # Staff fields
    organization_id = db.Column(db.String)
    organization = db.Column(db.String)
    unit_class = db.Column(db.String)
    unit_code = db.Column(db.String)
    unit = db.Column(db.String)

    # Student fields
    school_code = db.Column(db.String)
    school = db.Column(db.String)
    college_code = db.Column(db.String)
    curriculum = db.Column(db.String)
    office = db.Column(db.String)
    mailbox = db.Column(db.String)
    postal_address = db.Column(db.String)


    @staticmethod
    def search(criteria):
        print('Searching by criteria:')
        print(criteria)
        person_query = Person.query
        query = criteria.get('query')
        filters = criteria.get('filters')
        page = criteria.get('page')
        page_size = criteria.get('page_size')
        if query:
            person_query = Person.query_search(query)
        if filters:
            for category in filters:
                if category not in ('college', 'year', 'major', 'building_code', 'entryway',
                                    'floor', 'suite', 'room', 'state', 'leave', 'eli_whitney'):
                    return None
                if not isinstance(filters[category], list):
                    filters[category] = [filters[category]]
                person_query = person_query.filter(getattr(Person, category).in_(filters[category]))
        if page:
            students = person_query.paginate(page, page_size or app.config['PAGE_SIZE'], False).items
        else:
            students = person_query.all()
        return students
