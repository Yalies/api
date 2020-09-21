from app import app, db, celery
from app.models import Student
from .s3 import ImageUploader

from PIL import Image
from io import BytesIO
import os
import requests
import re
import json
from bs4 import BeautifulSoup
import usaddress
import yaledirectory


with open('app/res/majors.txt') as f:
    MAJORS = f.read().splitlines()
with open('app/res/major_full_names.json') as f:
    MAJOR_FULL_NAMES = json.load(f)
STATES = {}
with open('app/res/states.txt') as f:
    for line in f.read().splitlines():
        state, abbreviation = line.split('\t', 1)
        STATES[abbreviation.strip()] = state.strip()
RE_ROOM = re.compile(r'^([A-Z]+)-([A-Z]+)(\d+)(\d)([A-Z]+)?$')
RE_BIRTHDAY = re.compile(r'^[A-Z][a-z]{2} \d{1,2}$')
RE_ACCESS_CODE = re.compile(r'[0-9]-[0-9]+')
RE_PHONE = re.compile(r'[0-9]{3}-[0-9]{3}-[0-9]{4}')


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
    first_name, last_name = name.strip().split(', ', 1)
    return first_name, last_name


def clean_year(year):
    year = year.lstrip('\'')
    if not year:
        return None
    return 2000 + int(year)


def guess_email(student):
    return (student.first_name + '.' + student.last_name).replace(' ', '').lower() + '@yale.edu'


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
    watermark_mask = Image.open('app/res/watermark_mask.png')

    image_uploader = ImageUploader()

    # Clear all students
    Student.query.delete()
    for container in containers:
        student = Student()

        student.image_id = clean_image_id(container.find('img')['src'])

        if student.image_id is not None and student.image_id != 0:
            if student.image_id in image_uploader.image_ids:
                print('Student has image, but it has already been downloaded.')
            else:
                print('Image has not been uploaded yet.')
                image_r = requests.get('https://students.yale.edu/facebook/Photo?id=' + student.image_id,
                                       headers={
                                           'Cookie': face_book_cookie,
                                       },
                                       stream=True)
                image_r.raw.decode_content = True
                im = Image.open(image_r.raw)

                # Paste mask over watermark
                im.paste(watermark_mask, (0, 0), watermark_mask)

                output = BytesIO()
                im.save(output, format='JPEG', mode='RGB')

                student.image = image_uploader.upload_image(student.image_id, output)

        student.last_name, student.first_name = clean_name(container.find('h5', {'class': 'yalehead'}).text)
        student.year = clean_year(container.find('div', {'class': 'student_year'}).text)
        pronoun = container.find('div', {'class': 'student_info_pronoun'}).text
        student.pronoun = pronoun if pronoun else None

        info = container.find_all('div', {'class': 'student_info'})

        student.college = info[0].text.replace(' College', '')
        try:
            student.email = info[1].find('a').text
        except AttributeError:
            pass
            #student.email = guess_email(student)
        trivia = info[1].find_all(text=True, recursive=False)
        try:
            room = trivia.pop(0) if RE_ROOM.match(trivia[0]) else None
            if room:
                student.residence = room
                result = RE_ROOM.search(room)
                student.building_code, student.entryway, student.floor, student.suite, student.room = result.groups()
            student.birthday = trivia.pop() if RE_BIRTHDAY.match(trivia[-1]) else None
            student.major = trivia.pop() if trivia[-1] in MAJORS else None
            if student.major and student.major in MAJOR_FULL_NAMES:
                student.major = MAJOR_FULL_NAMES[student.major]
        except IndexError:
            pass

        new_trivia = []
        for r in range(len(trivia)):
            row = trivia[r].strip()
            if row.endswith(' /'):
                row = row.rstrip(' /')
                if RE_ACCESS_CODE.match(row):
                    student.access_code = row
                if RE_PHONE.match(row):
                    student.phone = row
                if len(new_trivia) == 1 and not student.residence:
                    student.residence = new_trivia.pop(0)
            else:
                new_trivia.append(row)
        trivia = new_trivia

        # Handle first row of address being duplicated for residence
        if len(trivia) >= 2 and trivia[0] == trivia[1] and not student.residence:
            student.residence = trivia.pop(0)

        student.address = '\n'.join(trivia)
        student.state = parse_address(student.address)

        directory_entry = directory.person(first_name=student.first_name, last_name=student.last_name)
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
