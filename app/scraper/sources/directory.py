from .source import Source

import yaledirectory
import requests
import re
import string
from threading import Thread


class Directory(Source):
    def __init__(self, cache, people_search_session_cookie, csrf_token):
        super().__init__(cache)
        self.directory = yaledirectory.API(people_search_session_cookie, csrf_token)

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

    directory_entries = []

    def get_directory_entry(self, person):
        query = {
            'first_name': person['first_name'],
            'last_name': person['last_name'],
            'school': 'YC'
        }
        if person.get('email'):
            query['email'] = person['email']
        if person.get('college'):
            query['college'] = person['college'] + ' College'
        people = self.directory.people(**query)
        print('Found %d matching people in directory.' % len(people))
        if not people:
            # If nothing found, do a broader search and return first result
            person = self.directory.person(first_name=person['first_name'], last_name=person['last_name'])
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

    def read_directory(self, prefix: str = ''):
        print('Attempting prefix ' + prefix)
        people, total = self.directory.people(netid=prefix, include_total=True)

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
        elif len(prefix) >= MAX_CHARS_IN_PREFIX and (len(prefix) != 0 and prefix[-1] in self.numbers):
            choices = self.numbers
        else:
            choices = self.characters

        res = []
        for choice in choices:
            res += self.read_directory(prefix + choice)
        return res

    def read_directory_async(self, prefix):
        directory_entries = self.read_directory(prefix=prefix)
        self.directory_entries += directory_entries

    def scrape(self, current_people):
        """
        Fetch new records and integrate.
        Overridden from normal scraping flow because we need to access existing records during scraping process.
        """
        people = []
        # Fetch non-undergrad users by iterating netids
        # Get set of netids for students we've already processed
        threads = []
        for prefix in self.letters:
            thread = Thread(target=self.read_directory_async, args=(prefix,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        for entry in self.directory_entries:
            # Remove ETRAIN_ accounts, which are not actual people
            if entry.netid.startswith('etrain'):
                continue
            print('Parsing directory entry with NetID ' + entry.netid)
            person = self.merge_one({}, entry)
            people.append(person)

        self.new_records = people
        print(self.new_records)

    #########
    # Merging
    #########

    def merge_one(self, person, entry):
        school = person.get('school') or entry.primary_school_name
        school = self.SCHOOL_OVERRIDES.get(school, school)
        school_code = person.get('school_code') or entry.primary_school_code
        if not school_code:
            school_code = self.SCHOOL_CODES.get(school)

        organization_code, organization = self.split_code_name(entry.organization_name)
        organization = self.ORGANIZATION_OVERRIDES.get(organization, organization)
        if not organization_code:
            organization_code = self.ORGANIZATION_CODES.get(organization)

        unit_class, unit = self.split_code_name(entry.organization_unit_name)
        office_building, office_room = self.split_office(entry.internal_location)
        person.update({
            'netid': entry.netid,
            'upi': entry.upi,
            'email': person.get('email') or entry.email,
            # Overwrite even names from the face book, which sometimes are capitalized improperly
            # For example "Del Carpio gomez, Victor"
            'first_name': entry.first_name,
            'last_name': entry.last_name,
            'title': entry.directory_title,
            'preferred_name': entry.known_as if entry.known_as != entry.first_name else None,
            'middle_name': entry.middle_name,
            'suffix': entry.suffix,
            'phone': person.get('phone') or self.clean_phone(entry.phone_number),
            # TODO: check if any face book members have a college but not a college code
            'college': person.get('college') or entry.residential_college_name.replace(' College', ''),
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
            # residential_college_name: from face book
        })
        if person['college'] == 'Undeclared':
            person['college'] = None
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

    def merge(self, current_people):
        checked_netids = {person_dict.get('netid') for person_dict in current_people if 'netid' in person_dict}
        new_entries = [
            person for person in self.new_records
            if 'netid' in person and person['netid'] not in checked_netids
        ]
        people = current_people + new_entries
        return people
