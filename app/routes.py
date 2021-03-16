from flask import render_template, request, jsonify, abort, g
from flask_cas import login_required
from app import app, db, scraper, cas
from app.models import User, Person, Key
from app.util import to_json, succ, fail
from app.cas_validate import validate
from sqlalchemy import distinct

import datetime
import time


with open('app/scraper/res/majors_clean.txt') as f:
    majors = f.read().splitlines()


@app.before_request
def store_user():
    if request.method != 'OPTIONS':
        if cas.username:
            g.user = User.query.get(cas.username)
            timestamp = int(time.time())
            if not g.user:
                g.user = User(id=cas.username,
                              registered_on=timestamp)
                db.session.add(g.user)
            g.user.last_seen = timestamp
            g.person = Person.query.filter_by(netid=cas.username, school_code='YC').first()
            if g.user.banned or (not g.person and not g.user.admin):
                # TODO: give a more graceful error than just a 403
                abort(403)
            try:
                print(g.person.first_name + ' ' + g.person.last_name)
            except AttributeError:
                print('Could not render name.')
            db.session.commit()


@app.route('/')
def index():
    if not cas.username:
        return render_template('splash.html')
    colleges = [
        'Berkeley',
        'Branford',
        'Davenport',
        'Ezra Stiles',
        'Jonathan Edwards',
        'Benjamin Franklin',
        'Grace Hopper',
        'Morse',
        'Pauli Murray',
        'Pierson',
        'Saybrook',
        'Silliman',
        'Timothy Dwight',
        'Trumbull',
    ]
    """
    building_codes = {
        '': 'Off Campus',
        'BM': 'Bingham Hall',
        'W': 'Welch Hall',
        'F': 'Farnam Hall',
        'D': 'Durfee Hall',
        'L': 'Lawrance Hall',
        'V': 'Vanderbilt Hall',
        'LW': 'Lanman-Wright Hall',
        'BK': 'Berkeley',
        'BR': 'Branford',
        'DC': 'Davenport',
        'ES': 'Ezra Stiles',
        'JE': 'Jonathan Edwards',
        'BF': 'Benjamin Franklin',
        'GH': 'Grace Hopper',
        'MC': 'Morse',
        'MY': 'Pauli Murray',
        'PC': 'Pierson',
        'SY': 'Saybrook',
        'SM': 'Silliman',
        'TD': 'Timothy Dwight',
        'TC': 'Trumbull',
    }
    """
    current_year = datetime.date.today().year
    years = list(range(current_year, current_year + 5))
    years.append('')
    leave = ['Yes', 'No']
    eli_whitney = ['Yes', 'No']
    # SQLAlchemy returns lists of tuples, so we gotta convert to a list of items.
    # TODO: is there a SQL-based way to do this?
    """
    entryways = untuple(db.session.query(distinct(Person.entryway)).order_by(Person.entryway))
    floors = untuple(db.session.query(distinct(Person.floor)).order_by(Person.floor))
    suites = untuple(db.session.query(distinct(Person.suite)).order_by(Person.suite))
    rooms = untuple(db.session.query(distinct(Person.room)).order_by(Person.room))
    """
    return render_template('index.html', colleges=colleges,
                           years=years, leave=leave, eli_whitney=eli_whitney, majors=majors)
    """
                           building_codes=building_codes,
                           entryways=entryways, floors=floors, suites=suites, rooms=rooms)
    """


@app.route('/scraper', methods=['GET', 'POST'])
@login_required
def scrape():
    if not g.user.admin:
        abort(403)
    if request.method == 'GET':
        return render_template('scraper.html')
    payload = request.get_json()
    scraper.scrape.apply_async(args=[payload['face_book_cookie'], payload['people_search_session_cookie'], payload['csrf_token']])
    return '', 200


@app.route('/apidocs')
@login_required
def apidocs():
    return render_template('apidocs.html')


@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/hide_me')
@login_required
def hide_me():
    return render_template('hide_me.html')


@app.route('/keys', methods=['GET'])
@login_required
def get_keys():
    keys = Key.query.filter_by(user_id=g.user.id,
                               deleted=False).all()
    return to_json(keys)


@app.route('/keys', methods=['POST'])
@login_required
def create_key():
    payload = request.get_json()
    key = g.user.create_key(payload['description'])
    db.session.add(key)
    db.session.commit()
    return to_json(key)


"""
@app.route('/keys/<key_id>', methods=['POST'])
@login_required
def update_key(key_id):
    pass
"""


@app.route('/keys/<key_id>', methods=['DELETE'])
@login_required
def delete_key(key_id):
    key = Key.query.get(key_id)
    if key.user_id != g.user.id:
        return fail('You may not delete this key.', 403)
    key.deleted = True
    db.session.commit()
    return succ('Key deleted.')


@app.route('/auth', methods=['POST'])
def auth():
    # TODO: merge with above function?
    payload = request.get_json()
    jsessionid = payload.get('jsessionid')
    if not jsessionid:
        abort(401)
    valid = validate(jsessionid)
    if not valid:
        abort(401)
    # Validation sets the user for this session, so we can re-query
    g.user = User.query.get(cas.username)
    description = 'Mobile login'
    key = Key.query.filter_by(id=g.user.id, description=description, internal=True)
    if key is None:
        key = g.user.create_key(description, internal=True)
        db.session.add(key)
        db.session.commit()
    return jsonify({'token': key.token, 'expires_in': expires_in})


"""
def untuple(tuples):
    return [t[0] for t in tuples]
"""
