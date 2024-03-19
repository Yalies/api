from app import app, db
from app.search import SearchableMixin
from app.util import get_now, PERSISTENT_FIELDS, scrub_hidden_data
import jwt
import datetime
from copy import copy
from sqlalchemy.sql import collate
from sqlalchemy.orm.session import make_transient


leaderships = db.Table(
    'leadership',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), nullable=False),
    db.Column('person_id', db.Integer, db.ForeignKey('person.id'), nullable=False),
)


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
        payload = {
            # TODO: when we don't offset it, timezone issues emerge. Would be better to fix those issues
            'iat': get_now() - 100_000,
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
            created_at=get_now(),
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
        key = Key.query.filter_by(token=token).first()
        if key is not None and key.approved:
            key.uses += 1
            key.last_used = get_now()
        try:
            payload = jwt.decode(token, app.config.get('SECRET_KEY'), algorithms=['HS256'])
            return User.query.get(payload['sub'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            # Signature expired, or token otherwise invalid
            return None


class Person(SearchableMixin, db.Model):
    __tablename__ = 'person'
    __searchable__ = (
        'first_name', 'last_name', 'netid', 'email', 'college_code', 'college', 'residence', 'major', 'upi', 'title',
        'preferred_name', 'middle_name', 'suffix', 'pronouns', 'address',
        'school_code', 'school', 'year', 'curriculum', 'organization_code', 'organization', 'unit_class', 'unit_code', 'unit',
        'postal_address', 'office_building', 'office_room',
    )
    __filterable_identifiable__ = (
        'netid', 'upi', 'email', 'mailbox', 'phone',
        'title', 'first_name', 'preferred_name', 'middle_name', 'last_name', 'suffix', 'pronouns',
        'access_code', 'residence', 'office_room',
    )
    __filterable__ = (
        'school_code', 'school', 'year', 'curriculum', 'college', 'college_code', 'leave',
        'birth_month', 'birth_day', 'building_code', 'entryway', 'floor', 'suite', 'room', 'major',
        'organization_code', 'organization', 'unit_class', 'unit_code', 'unit', 'office_building',
    )
    __serializable__ = (
        'netid', 'upi', 'email', 'mailbox', 'phone', 'fax',
        'title', 'first_name', 'preferred_name', 'middle_name', 'last_name', 'suffix', 'pronouns',
        'phonetic_name', 'name_recording',
        'school_code', 'school', 'year', 'curriculum',
        'college', 'college_code', 'leave', 'visitor', 'image', 'birthday', 'birth_month', 'birth_day',
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
    visitor = db.Column(db.Boolean)
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
            people = person_query.paginate(page=page, per_page=page_size or app.config['PAGE_SIZE']).items
        else:
            people = person_query.all()
        return people

    def get_persistent_data(self):
        return PersonPersistent.query.filter_by(person_id=self.id).first()

    @staticmethod
    def search_respect_privacy_include_persistent(criteria):
        '''
        Performs a search, including persistent data.
        - Persistent data, including privacy and social information, is returned.
        - If a person's privacy settings hide a certain field, it will be omitted from the results.
        - The returned objects will be expunged, and changes to them will not be committed.
        '''
        people = Person.search(criteria)
        people_copy = []
        for person in people:
            person_copy = copy(person)
            make_transient(person_copy)

            persistent_data = person.get_persistent_data()
            if persistent_data is not None:
                for field in PERSISTENT_FIELDS:
                    setattr(person_copy, field, getattr(persistent_data, field))
            
            scrub_hidden_data(person_copy)
            people_copy.append(person_copy)
        return people_copy

class PersonPersistent(db.Model):
    __tablename__ = 'person_persistent'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))

    # socials
    socials_instagram = db.Column(db.String)
    socials_snapchat = db.Column(db.String)

    # privacy
    privacy_hide_image = db.Column(db.Boolean)
    privacy_hide_email = db.Column(db.Boolean)
    privacy_hide_room = db.Column(db.Boolean)
    privacy_hide_phone = db.Column(db.Boolean)
    privacy_hide_address = db.Column(db.Boolean)
    privacy_hide_major = db.Column(db.Boolean)
    privacy_hide_birthday = db.Column(db.Boolean)
class Group(db.Model):
    __tablename__ = 'group'
    __searchable__ = (
        'name', 'email', 'address', 'website',
    )
    __filterable_identifiable__ = (
        'id', 'name', 'email',
    )
    __filterable__ = (
        'type', 'category',
    )
    __serializable__ = (
        'id', 'name', 'type', 'category', 'email', 'website', 'phone', 'logo', 'address',
        'mission', 'benefits', 'goals', 'constitution', 'leaders',
    )
    _to_expand = ('leaders')

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    type = db.Column(db.String)
    category = db.Column(db.String)
    website = db.Column(db.String)
    phone = db.Column(db.String)
    email = db.Column(db.String)
    logo = db.Column(db.String)
    address = db.Column(db.String)

    mission = db.Column(db.String)
    benefits = db.Column(db.String)
    goals = db.Column(db.String)
    constitution = db.Column(db.String)

    leaders = db.relationship(
        'Person', secondary=leaderships, lazy='subquery',
        backref=db.backref('group', lazy=True))

    @staticmethod
    def search(criteria):
        print('Searching by criteria:')
        print(criteria)
        group_query = Group.query
        query = criteria.get('query')
        filters = criteria.get('filters')
        page = criteria.get('page')
        page_size = criteria.get('page_size')
        """
        if query:
            group_query = Group.query_search(query)
        else:
            group_query = group_query.order_by(
                #collate(Person.last_name, 'NOCASE'),
                #collate(Person.first_name, 'NOCASE'),
                Person.last_name,
                Person.first_name,
            )
        """
        if filters:
            for category in filters:
                if category not in (Group.__filterable_identifiable__ + Group.__filterable__):
                    return None
                if not isinstance(filters[category], list):
                    filters[category] = [filters[category]]
                group_query = group_query.filter(getattr(Group, category).in_(filters[category]))
        if page:
            groups = group_query.paginate(page=page, per_page=page_size or app.config['PAGE_SIZE'], error_out=False).items
        else:
            groups = group_query.all()
        return groups


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
