from app import app, db, celery
from app.models import Person
from .s3 import ImageUploader

from PIL import Image
from io import BytesIO
import os
import requests
import re
import json
from bs4 import BeautifulSoup
import yaledirectory
from cryptography.fernet import Fernet


with open('app/res/majors.txt') as f:
    MAJORS = f.read().splitlines()
with open('app/res/major_full_names.json') as f:
    MAJOR_FULL_NAMES = json.load(f)
RE_ROOM = re.compile(r'^([A-Z]+)-([A-Z]+)(\d+)(\d)([A-Z]+)?$')
RE_BIRTHDAY = re.compile(r'^[A-Z][a-z]{2} \d{1,2}$')
RE_ACCESS_CODE = re.compile(r'[0-9]-[0-9]+')
RE_PHONE = re.compile(r'[0-9]{3}-[0-9]{3}-[0-9]{4}')

PRE2020_KEY = os.environ.get('PRE2020_KEY')


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
    return int(image_id)


def clean_name(name):
    print('Parsing ' + name)
    first_name, last_name = name.strip().split(', ', 1)
    return first_name, last_name


def clean_year(year):
    year = year.lstrip('\'')
    if not year:
        return None
    return 2000 + int(year)


def get_directory_entry(directory, person):
    query = {
        'first_name': person['first_name'],
        'last_name': person['last_name'],
        'school': 'YC'
    }
    if person.get('email'):
        query['email'] = person['email']
    if person.get('college'):
        query['college'] = person['college'] + ' College'
    people = directory.people(**query)
    print('Found %d matching people in directory.' % len(people))
    if not people:
        # If nothing found, do a broader search and return first result
        return directory.person(first_name=person['first_name'], last_name=person['last_name'])
    return people[0]


def add_directory_to_person(person, entry):
    if not person.get('netid'):
        person.update({
            'netid': entry.netid,
            'first_name': entry.first_name,
            'last_name': entry.last_name,
            'college': entry.residential_college_name,
            'upi': entry.upi,
            'email': entry.email,
        })
    person.update({
        'title': entry.directory_title,
        'nickname': entry.known_as,
        'middle_name': entry.middle_name,
        'suffix': entry.suffix,
        'phone': entry.phone_number,
        'college_code': entry.residential_college_code,
        'school': entry.primary_school_name,
        'school_code': entry.primary_school_code,
        # Review naming:
        'primary_organization': entry.primary_organization_name,
        'primary_organization_code': entry.primary_organization_code,
        'primary_organization_id': entry.primary_organization_id,
        'organization': entry.organization_name,
        'organization_unit': entry.organization_unit_name,
        'primary_division': entry.primary_division_name,
        'curriculum': entry.student_curriculum,
        'year': person['year'] or student_expected_graduation_year,
        'mailbox': entry.mailbox,
        'postal_address': entry.postal_address,
        # TODO: do we really want to merge these? Will there ever be both?
        'address': person.address or entry.student_address or entry.registered_address,
        'location': entry.internal_location,
    })
    return person


@celery.task
def scrape(face_book_cookie, people_search_session_cookie, csrf_token):
    html = get_html(face_book_cookie)
    tree = get_tree(html)
    containers = get_containers(tree)

    if len(containers) == 0:
        print('No people were found on this page. There may be something wrong with authentication, aborting.')
        return

    directory = yaledirectory.API(people_search_session_cookie, csrf_token)
    watermark_mask = Image.open('app/res/watermark_mask.png')

    image_uploader = ImageUploader()
    print('Already hosting {} images.'.format(len(image_uploader.image_ids)))

    person_emails = {}
    people = []

    for container in containers:
        person = {}

        person['last_name'], person['first_name'] = clean_name(container.find('h5', {'class': 'yalehead'}).text)
        person['image_id'] = clean_image_id(container.find('img')['src'])

        if person['image_id']:
            if person['image_id'] in image_uploader.image_ids:
                print('Person has image, but it has already been processed.')
                person['image'] = image_uploader.get_image_url(person['image_id'])
            else:
                print('Image has not been processed yet.')
                image_r = requests.get('https://students.yale.edu/facebook/Photo?id=' + str(person['image_id']),
                                       headers={
                                           'Cookie': face_book_cookie,
                                       },
                                       stream=True)
                image_r.raw.decode_content = True
                try:
                    im = Image.open(image_r.raw)

                    # Paste mask over watermark
                    im.paste(watermark_mask, (0, 0), watermark_mask)

                    output = BytesIO()
                    im.save(output, format='JPEG', mode='RGB')

                    person['image'] = image_uploader.upload_image(person['image_id'], output)
                except OSError:
                    # "Cannot identify image" error
                    print('PIL could not identify image.')

        person['year'] = clean_year(container.find('div', {'class': 'student_year'}).text)
        pronoun = container.find('div', {'class': 'student_info_pronoun'}).text
        person['pronoun'] = pronoun if pronoun else None

        info = container.find_all('div', {'class': 'student_info'})

        person['college'] = info[0].text.replace(' College', '')
        try:
            person['email'] = info[1].find('a').text
        except AttributeError:
            pass
            #person.email = guess_email(person)
        trivia = info[1].find_all(text=True, recursive=False)
        try:
            room = trivia.pop(0) if RE_ROOM.match(trivia[0]) else None
            if room:
                person['residence'] = room
                result = RE_ROOM.search(room)
                person['building_code'], person['entryway'], person['floor'], person['suite'], person['room'] = result.groups()
            person['birthday'] = trivia.pop() if RE_BIRTHDAY.match(trivia[-1]) else None
            person['major'] = trivia.pop() if trivia[-1] in MAJORS else None
            if person['major'] and person['major'] in MAJOR_FULL_NAMES:
                person['major'] = MAJOR_FULL_NAMES[person['major']]
        except IndexError:
            pass

        new_trivia = []
        for r in range(len(trivia)):
            row = trivia[r].strip()
            if row.endswith(' /'):
                row = row.rstrip(' /')
                if RE_ACCESS_CODE.match(row):
                    person['access_code'] = row
                if RE_PHONE.match(row):
                    person['phone'] = row
                if len(new_trivia) == 1 and not person.get('residence'):
                    person['residence'] = new_trivia.pop(0)
            else:
                new_trivia.append(row)
        trivia = new_trivia

        # Handle first row of address being duplicated for residence
        if len(trivia) >= 2 and trivia[0] == trivia[1] and not person.get('residence'):
            person['residence'] = trivia.pop(0)

        person['address'] = '\n'.join(trivia)

        directory_entry = get_directory_entry(directory, person)
        if directory_entry is not None:
            person['netid'] = directory_entry.netid
            person['upi'] = directory_entry.upi
            if not person.get('email'):
                person['email'] = directory_entry.email
            if not person.get('year') and directory_entry.student_expected_graduation_year:
                person['year'] = int(directory_entry.student_expected_graduation_year)
                # This may not always be the case. But it's probably a safe bet.
                person['eli_whitney'] = True
        else:
            print('Could not find directory entry.')

        if person.get('email'):
            person_emails[person['email']] = len(people)
        people.append(person)

    with open('app/res/pre2020.html.fernet', 'rb') as f:
        fernet = Fernet(PRE2020_KEY)
        html = fernet.decrypt(f.read())
    tree = get_tree(html)
    containers = get_containers(tree)

    for container in containers:
        year = clean_year(container.find('div', {'class': 'student_year'}).text)
        info = container.find_all('div', {'class': 'student_info'})
        try:
            email = info[1].find('a').text
        except AttributeError:
            continue
        if email in person_emails and year is not None and people[person_emails[email]]['year'] is not None:
            people[person_emails[email]]['leave'] = (year < people[person_emails[email]]['year'])
            print(email + ' is' + (' not' if not people[person_emails[email]]['leave'] else '') + ' taking a leave.')


    # Store people into database
    Person.query.delete()
    for person_dict in people:
        db.session.add(Person(**person_dict))
    db.session.commit()
    print('Done.')
