from flask import render_template, make_response, request, redirect, url_for, jsonify, abort, g, session
from app import app, db, scraper, cas
from app.models import User, Person, Key
from app.util import to_json, get_now, succ, fail
from .cas_validate import validate
from sqlalchemy import distinct

from flask_cas.cas_urls import create_cas_login_url
from flask_cas.cas_urls import create_cas_logout_url
from flask_cas.cas_urls import create_cas_validate_url

import datetime
import calendar
from functools import wraps


with open('app/scraper/res/majors_clean.txt') as f:
    majors = f.read().splitlines()


@app.before_request
def store_user():
    if request.method != 'OPTIONS':
        g.user = None
        timestamp = get_now()
        token_cookie = request.cookies.get('token')
        if token_cookie:
            g.user = User.from_token(token_cookie)
            method_used = 'cookie'
        authorization = request.headers.get('Authorization')
        if g.user is None and authorization:
            token = authorization.split(' ')[-1]
            g.user = User.from_token(token)
            method_used = 'header'
        if g.user is None and cas.username:
            g.user = User.query.get(cas.username)
            if not g.user:
                # If this is the first user (probably local run), there's been no chance to
                # run the scraper yet, so make them admin to prevent an instant 403.
                is_first_user = User.query.count() == 0
                g.user = User(id=cas.username,
                              registered_on=timestamp,
                              admin=is_first_user)
                db.session.add(g.user)
            method_used = 'CAS'
        if g.user:
            g.person = Person.query.filter_by(netid=g.user.id, school_code='YC').first()
            if g.user.banned or (not g.person and not g.user.admin):
                # TODO: give a more graceful error than just a 403
                abort(403)
            try:
                print(f'Authorized request by {g.person.first_name} {g.person.last_name} with {method_used} authentication.')
            except AttributeError:
                print('Could not render name.')
            g.user.last_seen = timestamp
            db.session.commit()
        else:
            print('Request made by unauthorized user.')


def requires_login(f):
    @wraps(f)
    def wrapper_requires_login(*args, **kwargs):
        if g.user is None:
            return fail('Missing or invalid authorization.', code=401)
        return f(*args, **kwargs)
    return wrapper_requires_login


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
    years = get_years()
    leave = ['Yes', 'No']
    birth_months = {index + 1: name for index, name in enumerate(list(calendar.month_name)[1:])}
    birth_days = list(range(1, 31 + 1))

    # TODO: should this be loaded from the filters endpoint?
    options = {}
    for category in Person.__filterable__:
        options[category] = untuple(db.session.query(distinct(getattr(Person, category))).order_by(getattr(Person, category)))

    filters = {
        'Students': {
            'school': {
                'header': 'School',
            },
            'year': {
                'header': 'Year',
            },
        },
        'Undergraduate': {
            'college': {
                'header': 'College',
            },
            'major': 'Major',
            'leave': {
                'header': 'Took Leave?',
                'default': 'N/A'
            },
            'birth_month': {
                'header': 'Birth Month',
            },
            'birth_day': {
                'header': 'Birth Day',
            },
        },
        'Graduate': {
            'curriculum': {
                'header': 'Grad Curriculum',
            },
        },
        'Staff': {
            'organization': {
                'header': 'Staff Organization',
            },
            'unit': {
                'header': 'Staff Unit',
            },
            'office_building': {
                'header': 'Office Building',
            },
        },
    }
    return render_template('index.html', colleges=colleges,
                           years=years, leave=leave, majors=majors,
                           birth_months=birth_months, birth_days=birth_days, options=options, filters=filters)



def untuple(tuples):
    return [t[0] for t in tuples]


@app.route('/login/')
def login():
    token = None

    # NOTE: most of this code is adapted from the flask_cas module, but has since been heavily modified.

    redirect_url = create_cas_login_url(
        app.config['CAS_SERVER'],
        app.config['CAS_LOGIN_ROUTE'],
        url_for('.login', _external=True))

    if 'ticket' in request.args:
        ticket = request.args['ticket']
        valid, username = validate(ticket)
        if not valid:
            abort(401)
        redirect_url = url_for(app.config['CAS_AFTER_LOGIN'])
        g.user = User.query.get(username)
        if g.user is None:
            # TODO: this is duplicated from above. Decrease ick
            g.user = User(id=username,
                          registered_on=get_now(),
                          admin=is_first_user)
            db.session.add(g.user)
        db.session.commit()
        token = g.user.generate_token()
        print('Logged in!')

    app.logger.debug('Redirecting to: {0}'.format(redirect_url))

    resp = make_response(redirect(redirect_url))
    if token is not None:
        resp.set_cookie('token', token, max_age=365 * 60 * 60 * 24)
    return resp


@app.route('/logout/')
def logout():
    cas_username_session_key = app.config['CAS_USERNAME_SESSION_KEY']
    cas_attributes_session_key = app.config['CAS_ATTRIBUTES_SESSION_KEY']

    if cas_username_session_key in flask.session:
        del flask.session[cas_username_session_key]

    if cas_attributes_session_key in flask.session:
        del flask.session[cas_attributes_session_key]

    redirect_url = app.config['CAS_AFTER_LOGOUT']

    app.logger.debug('Redirecting to: {0}'.format(redirect_url))

    resp = make_response(redirect(redirect_url))
    resp.set_cookie('token', '', expires=0)

    return resp


@app.route('/scraper', methods=['GET', 'POST'])
@requires_login
def scrape():
    if not g.user.admin:
        abort(403)
    if request.method == 'GET':
        return render_template('scraper.html')
    payload = request.get_json()
    scraper.scrape.apply_async(args=[payload['caches'], payload['face_book_cookie'], payload['people_search_session_cookie'], payload['csrf_token'], payload['yaleconnect_cookie']])
    return '', 200


@app.route('/apidocs')
@requires_login
def apidocs():
    return render_template('apidocs.html', title='API')


@app.route('/about')
@requires_login
def about():
    return render_template('about.html', title='About')


@app.route('/faq')
def faq():
    return render_template('faq.html', title='FAQ')


@app.route('/hide_me')
def hide_me():
    return redirect(url_for('faq'))


@app.route('/keys', methods=['GET'])
@requires_login
def get_keys():
    keys = Key.query.filter_by(user_id=g.user.id,
                               deleted=False).all()
    return to_json(keys)


@app.route('/keys', methods=['POST'])
@requires_login
def create_key():
    payload = request.get_json()
    key = g.user.create_key(payload['description'])
    db.session.add(key)
    db.session.commit()
    return to_json(key)


"""
@app.route('/keys/<key_id>', methods=['POST'])
@requires_login
def update_key(key_id):
    pass
"""


@app.route('/keys/<key_id>', methods=['DELETE'])
@requires_login
def delete_key(key_id):
    key = Key.query.get(key_id)
    if key.user_id != g.user.id:
        return fail('You may not delete this key.', 403)
    key.deleted = True
    db.session.commit()
    return succ('Key deleted.')


@app.route('/authorize', methods=['POST'])
def api_authorize_cas():
    ticket = request.args.get('ticket')
    if not ticket:
        print('Aborting due to missing ticket')
        abort(401)
    valid, username = validate(ticket)
    if not valid:
        print('Aborting due to invalid ticket')
        abort(401)
    print('Logged in!')
    g.user = User.query.get(username)
    db.session.commit()
    return to_json({'token': g.user.generate_token()})


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
