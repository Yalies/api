from app import app, db, celery
from app.models import Student

import os
import requests
import re
from bs4 import BeautifulSoup
import usaddress
import yaledirectory


with open('app/res/majors.txt') as f:
    MAJORS = f.read().splitlines()
STATES = {}
with open('app/res/states.txt') as f:
    for line in f.read().splitlines():
        state, abbreviation = line.split('\t', 1)
        STATES[abbreviation.strip()] = state.strip()
RE_ROOM = re.compile(r'^([A-Z]+)-([A-Z]+)(\d+)(\d)([A-Z]+)?$')
RE_BIRTHDAY = re.compile(r'^[A-Z][a-z]{2} \d{1,2}$')


def get_html(cookie):
    filename = 'page.html'
    if not os.path.exists(filename):
        print('Page not cached, fetching.')
        requests.get('https://students.yale.edu/facebook/ChangeCollege',
                     params={
                        'newOrg': 'Yale College'
                     },
                     headers={
                         'Cookie': cookie,
                     })
        r = requests.get('https://students.yale.edu/facebook/PhotoPageNew',
                         params={
                             'currentIndex': -1,
                             'numberToGet': -1,
                         },
                         headers={
                             'Cookie': cookie,
                         })
        html = r.text
        with open(filename, 'w') as f:
            f.write(html)
        print('Done fetching page.')
    else:
        print('Using cached page.')
        with open(filename, 'r') as f:
            html = f.read()
    return html


def get_tree(html):
    print('Building tree.')
    tree = BeautifulSoup(html, 'html.parser')
    print('Done building tree.')
    return tree


def get_containers(tree):
    return tree.find_all('div', {'class': 'student_container'})


def clean_image_id(image_src):
    image_id = image_src.lstrip('/facebook/Photo?id=')
    # Check if image is not found
    if image_id == 0:
        return None
    return image_id



def clean_name(name):
    print('Parsing ' + name)
    forename, surname = name.strip().split(', ', 1)
    return forename, surname


def clean_year(year):
    year = year.lstrip('\'')
    if not year:
        return None
    return 2000 + int(year)


def guess_email(student):
    return (student.forename + '.' + student.surname).replace(' ', '').lower() + '@yale.edu'


def parse_address(address):
    # Remove duplicates
    address = list(dict.fromkeys(address))
    address = ', '.join(address)
    try:
        components = usaddress.parse(address)
        options = [
            component for component, label in components
            if label == 'StateName' and component in STATES
        ]
        if options:
            return options[0]
    except usaddress.RepeatedLabelError:
        pass


@celery.task
def scrape(face_book_cookie, people_search_session_cookie, csrf_token):
    html = get_html(face_book_cookie)
    tree = get_tree(html)
    containers = get_containers(tree)

    directory = yaledirectory.API(people_search_session_cookie, csrf_token)

    # Clear all students
    Student.query.delete()
    for container in containers:
        student = Student()

        student.image_id = clean_image_id(container.find('img')['src'])
        student.surname, student.forename = clean_name(container.find('h5', {'class': 'yalehead'}).text)
        student.year = clean_year(container.find('div', {'class': 'student_year'}).text)
        student.pronoun = container.find('div', {'class': 'student_info_pronoun'}).text

        info = container.find_all('div', {'class': 'student_info'})

        student.college = info[0].text.replace(' College', '')
        try:
            student.email = info[1].find('a').text
        except AttributeError:
            pass
        trivia = info[1].find_all(text=True, recursive=False)
        try:
            room = trivia.pop(0) if RE_ROOM.match(trivia[0]) else None
            if room:
                student.residence = room
                result = RE_ROOM.search(room)
                student.building_code, student.entryway, student.floor, student.suite, student.room = result.groups()
            student.birthday = trivia.pop() if RE_BIRTHDAY.match(trivia[-1]) else None
            student.major = trivia.pop() if trivia[-1] in MAJORS else None
            student.address = ', '.join(trivia)
            student.state = parse_address(trivia)
        except IndexError:
            pass

        directory_entry = directory.person(first_name=student.forename, last_name=student.surname)
        if directory_entry is not None:
            student.netid = directory_entry.netid
            student.upi = directory_entry.upi
            if not student.email:
                student.email = directory_entry.email
                #student.email = guess_email(student)
            if not student.year:
                student.year = directory_entry.student_expected_graduation_year
        else:
            print('Could not find directory entry.')

        db.session.add(student)

    with open('pre2020.html', 'r') as f:
        html = f.read()
    tree = get_tree(html)
    containers = get_containers(tree)

    for container in containers:
        year = clean_year(container.find('div', {'class': 'student_year'}).text)
        info = container.find_all('div', {'class': 'student_info'})
        try:
            email = info[1].find('a').text
        except AttributeError:
            continue
        student = Student.query.filter_by(email=email).first()
        if student is not None and year is not None and student.year is not None:
            student.leave = (year < student.year)

    db.session.commit()
    print('Done.')
