from app import app, db
from app.search import SearchableMixin
import jwt
import datetime
from sqlalchemy.sql import collate


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.String, primary_key=True)
    registered_on = db.Column(db.Integer)
    last_seen = db.Column(db.Integer)
    admin = db.Column(db.Boolean, default=False)
    banned = db.Column(db.Boolean, default=False)

    keys = db.relationship('Key', cascade='all,delete', back_populates='user')

    def generate_token(self):
        """
        Generate auth token.
        :return: token and expiration timestamp.
        """
        now = int(datetime.datetime.utcnow().timestamp())
        payload = {
            'iat': now,
            'sub': self.id,
        }
        return jwt.encode(
            payload,
            app.config.get('SECRET_KEY'),
            algorithm='HS256'
        )

    def create_key(self, description, internal=False):
        """
        Generate new API key object.
        :param description: description to add to the key.
        :return: newly created key object associated with this user.
        """
        token = self.generate_token()
        key = Key(
            token=token,
            description=description,
            internal=internal,
            created_at=int(datetime.datetime.utcnow().timestamp())
        )
        key.approved = True
        self.keys.append(key)
        return key

    @staticmethod
    def from_token(token):
        """
        Decode/validate an auth token.
        :param token: token to decode.
        :return: User whose token this is, or None if token invalid/no user associated
        """
        try:
            key = Key.query.filter_by(token=token).first()
            if key is None or not key.approved:
                return None
            key.uses += 1
            key.last_used = int(datetime.datetime.utcnow().timestamp())
            payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=['HS256'])
            return User.query.get(payload['sub'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            # Signature expired, or token otherwise invalid
            return None


class Person(SearchableMixin, db.Model):
    __tablename__ = 'person'
    __searchable__ = ('first_name', 'last_name', 'netid', 'college', 'email', 'residence', 'major', 'address')
    __filterable_identifiable__ = (
        'netid', 'upi', 'email', 'mailbox', 'phone',
        'title', 'first_name', 'preferred_name', 'middle_name', 'last_name', 'suffix', 'pronouns',
        'access_code', 'residence', 'office_room',
    )
    __filterable__ = (
        'school_code', 'school', 'year', 'curriculum', 'college', 'college_code', 'leave', 'eli_whitney',
        'birth_month', 'birth_day', 'building_code', 'entryway', 'floor', 'suite', 'room', 'major',
        'organization_code', 'organization', 'unit_class', 'unit_code', 'unit', 'office_building',
    )
    __serializable__ = (
        'netid', 'upi', 'email', 'mailbox', 'phone', 'fax',
        'title', 'first_name', 'preferred_name', 'middle_name', 'last_name', 'suffix', 'pronouns',
        'phonetic_name', 'name_recording',
        'school_code', 'school', 'year', 'curriculum',
        'college', 'college_code', 'leave', 'eli_whitney', 'image', 'birthday', 'birth_month', 'birth_day',
        'residence', 'building_code', 'entryway', 'floor', 'suite', 'room',
        'major', 'address', 'access_code',
        'organization_code', 'organization', 'unit_class', 'unit_code', 'unit',
        'postal_address', 'office_building', 'office_room',
        'cv', 'profile', 'website', 'education', 'publications',
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # Identifiers
    netid = db.Column(db.String)
    upi = db.Column(db.Integer)
    email = db.Column(db.String)
    mailbox = db.Column(db.String)
    phone = db.Column(db.String)
    fax = db.Column(db.String)

    # Naming
    title = db.Column(db.String)
    first_name = db.Column(db.String, nullable=False)
    preferred_name = db.Column(db.String)
    middle_name = db.Column(db.String)
    last_name = db.Column(db.String, nullable=False)
    suffix = db.Column(db.String)
    pronouns = db.Column(db.String)

    phonetic_name = db.Column(db.String)
    name_recording = db.Column(db.String)

    # Miscellaneous
    address = db.Column(db.String)

    # Students
    school_code = db.Column(db.String)
    school = db.Column(db.String)
    year = db.Column(db.Integer)
    curriculum = db.Column(db.String)
    # Undergrads
    college = db.Column(db.String)
    college_code = db.Column(db.String)
    leave = db.Column(db.Boolean)
    eli_whitney = db.Column(db.Boolean)
    image = db.Column(db.String)
    birthday = db.Column(db.String)
    birth_month = db.Column(db.Integer)
    birth_day = db.Column(db.Integer)
    residence = db.Column(db.String)
    building_code = db.Column(db.String)
    entryway = db.Column(db.String)
    floor = db.Column(db.Integer)
    suite = db.Column(db.Integer)
    room = db.Column(db.String)
    major = db.Column(db.String)
    access_code = db.Column(db.String)

    # Staff
    organization_code = db.Column(db.String)
    organization = db.Column(db.String)
    unit_class = db.Column(db.String)
    unit_code = db.Column(db.String)
    unit = db.Column(db.String)
    postal_address = db.Column(db.String)
    office_building = db.Column(db.String)
    office_room = db.Column(db.String)
    cv = db.Column(db.String)
    profile = db.Column(db.String)
    website = db.Column(db.String)
    education = db.Column(db.String)
    publications = db.Column(db.String)

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
        else:
            person_query = person_query.order_by(
                #collate(Person.last_name, 'NOCASE'),
                #collate(Person.first_name, 'NOCASE'),
                Person.last_name,
                Person.first_name,
            )
        if filters:
            for category in filters:
                if category not in (Person.__filterable_identifiable__ + Person.__filterable__):
                    return None
                if not isinstance(filters[category], list):
                    filters[category] = [filters[category]]
                person_query = person_query.filter(getattr(Person, category).in_(filters[category]))
        if page:
            people = person_query.paginate(page, page_size or app.config['PAGE_SIZE'], False).items
        else:
            people = person_query.all()
        return people


class Key(db.Model):
    __tablename__ = 'key'
    __serializable__ = ('id', 'token', 'uses', 'description', 'created_at', 'last_used')
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String, unique=True, nullable=False)
    uses = db.Column(db.Integer, default=0)
    description = db.Column(db.String, nullable=False)
    internal = db.Column(db.Boolean, default=False)
    approved = db.Column(db.Boolean, nullable=False)
    deleted = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.Integer)
    last_used = db.Column(db.Integer)

    user_id = db.Column(db.String, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='keys')
