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
import string
from cryptography.fernet import Fernet


RE_ROOM = re.compile(r'^([A-Z]+)-([A-Z]+)(\d+)(\d)([A-Z]+)?$')
RE_BIRTHDAY = re.compile(r'^[A-Z][a-z]{2} \d{1,2}$')
RE_ACCESS_CODE = re.compile(r'[0-9]-[0-9]+')
RE_PHONE = re.compile(r'[0-9]{3}-[0-9]{3}-[0-9]{4}')

FERNET_KEY = os.environ.get('FERNET_KEY')

with open('app/res/majors.txt') as f:
    MAJORS = f.read().splitlines()
with open('app/res/major_full_names.json') as f:
    MAJOR_FULL_NAMES = json.load(f)

SCHOOL_OVERRIDES = {
    'School of Law': 'Law School',
    'Graduate School of Arts & Sci': 'Graduate School of Arts & Sciences',
}
SCHOOL_CODES = {
    'Divinity School': 'DI',
    'Graduate School of Arts & Sciences': 'GS',
    'Law School': 'LW',
    'School of Management': 'MG',
    'School of Medicine': 'MD',
    'School of Nursing': 'NR',
    'School of the Environment': 'FS',
    'School of Public Health': 'PH',
}
ORGANIZATION_OVERRIDES = {
    'School of Law': 'Law School',
    'School of Divinity': 'Divinity School',
    'Yale School of the Environment': 'School of the Environment',
    'Graduate School': 'Graduate School of Arts & Sciences',
    'Graduate School of Arts & Sci': 'Graduate School of Arts & Sciences',
}
ORGANIZATION_CODES = {
    'School of Management': 'SOM',
    'Divinity School': 'DIV',
    'Law School': 'LAW',
    'School of Medicine': 'MED',
    'School of Nursing': 'NUR',

    # Not in directory, but used in YDN articles
    'School of Public Health': 'SPH',
    'School of the Environment': 'ENV',
}


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
        person = directory.person(first_name=person['first_name'], last_name=person['last_name'])
        if person:
            print('Found matching person searching only by name.')
        return person
    return people[0]


def compare_years(page_key, people, emails):
    print(f'Comparing years from {page_key} store.')
    with open(f'app/res/{page_key}.html.fernet', 'rb') as f:
        fernet = Fernet(FERNET_KEY)
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
        if email in emails and not people[emails[email]].get('leave') and email in emails and year is not None and people[emails[email]]['year'] is not None:
            people[emails[email]]['leave'] = (year < people[emails[email]]['year'])
            print(email + ' is' + (' not' if not people[emails[email]]['leave'] else '') + ' taking a leave.')
    return people


def split_code_name(combined):
    if not combined:
        return None, None
    ID_RE = re.compile(r'^[A-Z_]+$')
    id, name = combined.split(' ', 1)
    if ID_RE.match(id):
        return id, name
    return '', combined


def clean_phone(phone):
    if not phone:
        return phone
    if type(phone) == int:
        phone = str(phone)
    COUNTRY_CODE_RE = re.compile('^\+1? ')
    phone = COUNTRY_CODE_RE.sub('', phone)
    DISALLOWED_CHARACTERS_RE = re.compile(r'[\(\) \-]')
    phone = DISALLOWED_CHARACTERS_RE.sub('', phone)
    return phone

def split_office(office):
    components = office.split(' > ')
    office_building = components[0]
    office_room = None
    if len(components) > 1:
        office_room = components[1]
    return office_building, office_room


def add_directory_to_person(person, entry):
    if not person.get('netid'):
        person.update({
            'netid': entry.netid,
            'college': entry.residential_college_name.replace(' College', ''),
            'upi': entry.upi,
            'email': entry.email,
        })

    school = person.get('school') or entry.primary_school_name
    school = SCHOOL_OVERRIDES.get(school, school)
    school_code = person.get('school_code') or entry.primary_school_code
    if not school_code:
        school_code = SCHOOL_CODES.get(school)

    organization_code, organization = split_code_name(entry.organization_name)
    organization = ORGANIZATION_OVERRIDES.get(organization, organization)
    if not organization_code:
        organization_code = ORGANIZATION_CODES.get(organization)

    unit_class, unit = split_code_name(entry.organization_unit_name)
    office_building, office_room = split_office(entry.internal_location)
    person.update({
        # Overwrite even names from the face book, which sometimes are capitalized improperly
        # For example "Del Carpio gomez, Victor"
        'first_name': entry.first_name,
        'last_name': entry.last_name,
        'title': entry.directory_title,
        'preferred_name': entry.known_as if entry.known_as != entry.first_name else None,
        'middle_name': entry.middle_name,
        'suffix': entry.suffix,
        'phone': person.get('phone') or clean_phone(entry.phone_number),
        # TODO: check if any face book members have a college but not a college code
        'college_code': entry.residential_college_code,
        'school': school,
        'school_code': school_code,
        'organization_code': organization_code,
        'organization': organization,
        'unit_class': unit_class,
        'unit': unit,
        'unit_code': entry.primary_organization_code,
        'curriculum': entry.student_curriculum,
        'mailbox': entry.mailbox,
        'postal_address': entry.postal_address,
        # TODO: do we really want to merge these? Will there ever be both?
        'address': person.get('address') or entry.student_address or entry.registered_address,
        # TODO: should we split the room number into a separate column?
        'office_building': office_building,
        'office_room': office_room,
        # Unused properties:
        # primary_organization_name: always the same as organization_unit
        # primary_organization_id: always empty
        # primary_division_name: always the same as organization_name
        # display_name, matched: useless
        # residential_college_name, student_expected_graduation_year: useless or from face book
    })
    if person['organization'] and not person['organization_code'] and person['school_code']:
        # This is a student, but their organization is still listed.
        # Remove their organization field, which is duplicated `school`.
        # This way, organization and related fields are used only for staff.
        person['organization'] = None

    if entry.primary_organization_name != entry.organization_unit_name:
        print('Warning: primary_organization_name and organization_unit_name are different!')
    if entry.organization_name != entry.primary_division_name:
        print('Warning: organization_name and primary_division_name are diferent!')
    if not person.get('year') and entry.student_expected_graduation_year:
        person['year'] = int(entry.student_expected_graduation_year)
    return person


letters = string.ascii_lowercase
numbers = string.digits
characters = letters + numbers


def read_directory(directory, prefix: str = ''):
    print('Attempting prefix ' + prefix)
    people, total = directory.people(netid=prefix, include_total=True)

    if total == len(people):
        print(f'Successfully found {total} people.')
        return people
    print(f'Found {total} people; trying more specific prefixes.')

    # NetIds have 2-3 characters followed by any amount of numbers.
    MIN_CHARS_IN_PREFIX = 2
    MAX_CHARS_IN_PREFIX = 3
    if len(prefix) < MIN_CHARS_IN_PREFIX:
        choices = letters
    elif len(prefix) >= MAX_CHARS_IN_PREFIX or (len(prefix) != 0 and prefix[-1] not in letters):
        choices = numbers
    else:
        choices = characters

    res = []
    for choice in choices:
        res += read_directory(directory, prefix + choice)
    return res


@celery.task
def scrape(face_book_cookie, people_search_session_cookie, csrf_token):
    # Uncomment for quick testing
    """
    directory = yaledirectory.API(people_search_session_cookie, csrf_token)
    people = []
    directory_entries = read_directory(directory, 'aa')
    for entry in directory_entries:
        print('Parsing directory entry with NetID ' + entry.netid)
        person = add_directory_to_person({}, entry)
        people.append(person)
    """


    html = get_html(face_book_cookie)
    tree = get_tree(html)
    containers = get_containers(tree)

    if len(containers) == 0:
        print('No people were found on this page. There may be something wrong with authentication, aborting.')
        return

    directory = yaledirectory.API(people_search_session_cookie, csrf_token)
    watermark_mask = Image.open('app/res/watermark_mask.png')

    image_uploader = ImageUploader()
    print('Already hosting {} images.'.format(len(image_uploader.files)))

    emails = {}
    people = []

    for container in containers:
        person = {
            'school': 'Yale College',
            'school_code': 'YC',
        }

        person['last_name'], person['first_name'] = clean_name(container.find('h5', {'class': 'yalehead'}).text)
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
                    person['phone'] = clean_phone(row)
                if len(new_trivia) == 1 and not person.get('residence'):
                    person['residence'] = new_trivia.pop(0)
            else:
                new_trivia.append(row)
        trivia = new_trivia

        # Handle first row of address being duplicated for residence
        if len(trivia) >= 2 and trivia[0] == trivia[1] and not person.get('residence'):
            person['residence'] = trivia.pop(0)

        person['address'] = '\n'.join(trivia)

        person['leave'] = False
        person['eli_whitney'] = False

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
            person = add_directory_to_person(person, directory_entry)
        else:
            print('Could not find directory entry.')

        image_id = clean_image_id(container.find('img')['src'])
        if image_id:
            image_filename = image_uploader.get_image_filename(image_id, person)
            if image_filename in image_uploader.files:
                person['image'] = image_uploader.get_image_url(image_filename)
            else:
                print('Image has not been processed yet.')
                image_r = requests.get('https://students.yale.edu/facebook/Photo?id=' + str(image_id),
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

                    person['image'] = image_uploader.upload_image(output, image_filename)
                except OSError:
                    # "Cannot identify image" error
                    print('PIL could not identify image.')

        if person.get('email'):
            emails[person['email']] = len(people)
        people.append(person)

    # Check leaves
    people = compare_years('pre2020', people, emails)
    people = compare_years('fall2020', people, emails)

    # Fetch non-undergrad users by iterating netids
    # Get set of netids for students we've already processed
    checked_netids = {person_dict.get('netid') for person_dict in people if 'netid' in person_dict}
    directory_entries = read_directory(directory)
    for entry in directory_entries:
        if entry.netid not in checked_netids:
            print('Parsing directory entry with NetID ' + entry.netid)
            checked_netids.add(entry.netid)
            person = add_directory_to_person({}, entry)
            people.append(person)

    # Store people into database
    Person.query.delete()
    for person_dict in people:
        db.session.add(Person(**{k: v for k, v in person_dict.items() if v or type(v) == bool}))
    db.session.commit()
    print('Done.')
