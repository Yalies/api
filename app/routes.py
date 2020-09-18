from flask import render_template, request, jsonify, g
from flask_cas import login_required
from app import app, db, tasks, cas
from app.models import User, Student
from sqlalchemy import distinct

import datetime
import time


with open('app/res/majors.txt') as f:
    majors = f.read().splitlines()
states = {}
with open('app/res/states.txt') as f:
    for line in f.read().splitlines():
        state, abbreviation = line.split('\t', 1)
        states[abbreviation.strip()] = state.strip()
states[''] = 'International/Other'


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
            db.session.commit()
            print('NetID: ' + cas.username)


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
    entryways = db.session.query(distinct(Student.entryway)).order_by(Student.entryway)
    floors = db.session.query(distinct(Student.floor)).order_by(Student.floor)
    suites = db.session.query(distinct(Student.suite)).order_by(Student.suite)
    rooms = db.session.query(distinct(Student.room)).order_by(Student.room)
    # SQLAlchemy returns lists of tuples, so we gotta convert to a list of items.
    # TODO: is there a SQL-based way to do this?
    entryways = untuple(entryways)
    floors = untuple(floors)
    suites = untuple(suites)
    rooms = untuple(rooms)
    return render_template('index.html', colleges=colleges,
                           years=years, leave=leave, majors=majors, building_codes=building_codes,
                           entryways=entryways, floors=floors, suites=suites, rooms=rooms, states=states)


@app.route('/query', methods=['POST'])
@login_required
def query():
    filters = request.get_json()
    students_query = Student.query
    for category in filters:
        if category not in ('college', 'year', 'major', 'building_code',
                            'entryway', 'floor', 'suite', 'room', 'state', 'leave'):
            abort(403)
        students_query = students_query.filter(getattr(Student, category).in_(filters[category]))
    students = students_query.all()
    return jsonify([student.email for student in students if student.email])


@app.route('/scraper', methods=['GET', 'POST'])
@login_required
def scraper():
    if cas.username != 'ekb33':
        abort(403)
    if request.method == 'GET':
        return render_template('scraper.html')
    payload = request.get_json()
    tasks.scrape.apply_async(args=[payload['cookie']])
    return '', 200


def untuple(tuples):
    return [t[0] for t in tuples]
