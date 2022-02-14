from flask import render_template, request, redirect, url_for, jsonify, abort, g
from flask_cas import login_required
from app import app, db, scraper, cas
from app.models import User, Person, Key
from app.util import to_json, succ, fail
from app.cas_validate import validate
from sqlalchemy import distinct

import datetime
import time
import calendar


with open('app/scraper/res/majors_clean.txt') as f:
    majors = f.read().splitlines()


@app.before_request
def store_user():
    if request.method != 'OPTIONS':
        if cas.username:
            g.user = User.query.get(cas.username)
            timestamp = int(time.time())
            if not g.user:
                # If this is the first user (probably local run), there's been no chance to
                # run the scraper yet, so give them admin to prevent an instant 403.
                is_first_user = User.query.count() == 0
                g.user = User(id=cas.username,
                              registered_on=timestamp,
                              admin=is_first_user)
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
    years = get_years()
    leave = ['Yes', 'No']
    birth_months = {index + 1: name for index, name in enumerate(list(calendar.month_name)[1:])}
    birth_days = list(range(1, 31 + 1))
    # SQLAlchemy returns lists of tuples, so we gotta convert to a list of items.
    # TODO: is there a SQL-based way to do this?
    """
    entryways = untuple(db.session.query(distinct(Person.entryway)).order_by(Person.entryway))
    floors = untuple(db.session.query(distinct(Person.floor)).order_by(Person.floor))
    suites = untuple(db.session.query(distinct(Person.suite)).order_by(Person.suite))
    rooms = untuple(db.session.query(distinct(Person.room)).order_by(Person.room))
    """
    return render_template('index.html', colleges=colleges,
                           years=years, leave=leave, majors=majors,
                           birth_months=birth_months, birth_days=birth_days)
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
    scraper.scrape.apply_async(args=[payload['caches'], payload['face_book_cookie'], payload['people_search_session_cookie'], payload['csrf_token']])
    return '', 200


@app.route('/apidocs')
@login_required
def apidocs():
    return render_template('apidocs.html')


@app.route('/about')
@login_required
def about():
    return render_template('about.html')


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/hide_me')
def hide_me():
    return redirect(url_for('faq'))


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


def get_years():
    """
    returns list of currently enrolled class years
    After May, the oldest class should be removed
    After July, the next class should be added
    e.g.:
    in January 2021: years = [2021, 2022, 2023, 2024]
    in July 2021: years = [2022, 2023, 2024]
    in September 2021: years = [2022, 2023, 2024, 2025]
    """
    GRAD_MONTH = 5  # May
    ADD_MONTH = 8   # August
    NUM_CLASSES = 4
    current_date = datetime.date.today()
    oldest_class_year = current_date.year if current_date.month <= GRAD_MONTH else current_date.year + 1
    youngest_class_year = current_date.year + NUM_CLASSES if current_date.month >= ADD_MONTH else current_date.year + NUM_CLASSES - 1
    years = list(range(oldest_class_year, youngest_class_year + 1))
    years.append('')
    return years
