from flask import render_template, request, jsonify, g
from flask_cas import login_required
from app import app, db, tasks, cas
from app.models import User, Student
from sqlalchemy import distinct

import datetime
import time


with open('app/res/majors_clean.txt') as f:
    majors = f.read().splitlines()


@app.before_request
def store_user():
    if request.method != 'OPTIONS':
        if cas.username:
            g.user = User.query.get(cas.username)
            timestamp = int(time.time())
            if not g.user:
                g.user = User(username=cas.username,
                              registered_on=timestamp)
                db.session.add(g.user)
            g.user.last_seen = timestamp
            g.student = Student.query.filter_by(netid=cas.username).first()
            if not g.student:
                # TODO: give a more graceful error than just a 403
                abort(403)
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
    current_year = datetime.date.today().year
    years = list(range(current_year, current_year + 5))
    years.append('')
    leave = ['Yes', 'No']
    eli_whitney = ['Yes', 'No']
    # SQLAlchemy returns lists of tuples, so we gotta convert to a list of items.
    # TODO: is there a SQL-based way to do this?
    entryways = untuple(db.session.query(distinct(Student.entryway)).order_by(Student.entryway))
    floors = untuple(db.session.query(distinct(Student.floor)).order_by(Student.floor))
    suites = untuple(db.session.query(distinct(Student.suite)).order_by(Student.suite)
    rooms = untuple(db.session.query(distinct(Student.room)).order_by(Student.room)
    return render_template('index.html', colleges=colleges,
                           years=years, leave=leave, eli_whitney=eli_whitney, majors=majors, building_codes=building_codes,
                           entryways=entryways, floors=floors, suites=suites, rooms=rooms, states=states)


@app.route('/scraper', methods=['GET', 'POST'])
@login_required
def scraper():
    if cas.username != 'ekb33':
        abort(403)
    if request.method == 'GET':
        return render_template('scraper.html')
    payload = request.get_json()
    tasks.scrape.apply_async(args=[payload['face_book_cookie'], payload['people_search_session_cookie'], payload['csrf_token']])
    return '', 200


@app.route('/apidocs')
@login_required
def apidocs():
    return render_template('apidocs.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/hide_me')
@login_required
def hide_me():
    return render_template('hide_me.html')


@app.route('/token', methods=['POST'])
@login_required
def get_token():
    token, expires_in = g.user.generate_token()
    return jsonify({'token': token, 'expires_in': expires_in})


def untuple(tuples):
    return [t[0] for t in tuples]
