from app import app, db


class User(db.Model):
    __tablename__ = 'users'

    username = db.Column(db.String, primary_key=True)
    registered_on = db.Column(db.Integer)
    last_seen = db.Column(db.Integer)


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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
