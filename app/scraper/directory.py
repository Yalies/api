from .source import Source

import yaledirectory
import requests
import re


class Directory(Source):
    def __init__(self, people_search_session_cookie, csrf_token):
        directory = yaledirectory.API(people_search_session_cookie, csrf_token)

    ##########
    # Scraping
    ##########

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

    letters = string.ascii_lowercase
    numbers = string.digits
    characters = letters + numbers

    def get_directory_entry(self, directory, person):
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

    def split_code_name(self, combined):
        if not combined:
            return None, None
        ID_RE = re.compile(r'^[A-Z_]+$')
        id, name = combined.split(' ', 1)
        if ID_RE.match(id):
            return id, name
        return '', combined

    def split_office(self, office):
        components = office.split(' > ')
        office_building = components[0]
        office_room = None
        if len(components) > 1:
            office_room = components[1]
        return office_building, office_room

    def read_directory(self, directory, prefix: str = ''):
        print('Attempting prefix ' + prefix)
        people, total = directory.people(netid=prefix, include_total=True)

        if total == len(people):
            print(f'Successfully found {total} people.')
            return people
        print(f'Found {total} people; trying more specific prefixes.')

        # NetIds have 2-3 characters followed by any amount of numbers.
        # Some emeritus professors have longer strings of letters without numbers, such as 'frhole'
        MIN_CHARS_IN_PREFIX = 2
        MAX_CHARS_IN_PREFIX = 3
        if len(prefix) < MIN_CHARS_IN_PREFIX:
            choices = self.letters
        elif len(prefix) >= MAX_CHARS_IN_PREFIX or (len(prefix) != 0 and prefix[-1] not in letters):
            choices = self.numbers
        else:
            choices = self.characters

        res = []
        for choice in choices:
            res += self.read_directory(directory, prefix + choice)
        return res

    def scrape(self):
        for i, person in enumerate(people):
            directory_entry = self.get_directory_entry(directory, person)
            if directory_entry is not None:
                person['netid'] = directory_entry.netid
                person['upi'] = directory_entry.upi
                if not person.get('email'):
                    person['email'] = directory_entry.email
                if not person.get('year') and directory_entry.student_expected_graduation_year:
                    person['year'] = int(directory_entry.student_expected_graduation_year)
                    # This may not always be the case. But it's probably a safe bet.
                    person['eli_whitney'] = True
                people[i] = add_directory_to_person(person, directory_entry)
            else:
                print('Could not find directory entry.')

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
            emails.append(person['email'])

    #########
    # Merging
    #########

    def merge_one(self, person, entry):
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


