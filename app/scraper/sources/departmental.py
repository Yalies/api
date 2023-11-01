from .source import Source
from app.scraper.sources import adapters
#import adapters

import json
import hashlib
from math import ceil
from threading import Thread
from app.scraper.sources import adapters
#import adapters
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


class Departmental(Source):

    ##########
    # Scraping
    ##########

    ADAPTERS = {
        None: adapters.Default(),
        'architecture': adapters.Architecture(),
        'environment': adapters.Environment(),
        'jackson': adapters.Jackson(),
        'law': adapters.Law(),
        'management': adapters.Management(),
        'medicine': adapters.Medicine(),
        'nursing': adapters.Nursing(),
        'seas': adapters.Seas(),
    }
    new_records = None
    department_queue = None

    NUM_THREADS = 3

    def scrape_department(self, department):
        logger.info('Scraping department: ' + department['name'])
        website_type = department.get('website_type')
        adapter = self.ADAPTERS.get(website_type)
        new_records = adapter.scrape(department)
        self.new_records += new_records

    def scrape_departments(self, departments):
        for department in departments:
            self.scrape_department(department)

    def scrape_department_queue(self):
        while len(self.department_queue) > 0:
            department = self.department_queue.pop()
            self.scrape_department(department)

    def scrape(self, current_people):
        # TEMPORARY
        # For testing with local JSON file
        #with open('/tmp/people.json', 'r') as f:
        #    people = json.load(f)
        #return people

        with open('app/scraper/res/departments.json', 'r') as f:
            departments = json.load(f)
        # If any departments have been marked enabled, filter to just them
        enabled_departments = [department for department in departments if department.get('enabled')]
        if enabled_departments:
            departments = enabled_departments
        self.department_queue = departments

        self.new_records = []
        threads = []
        for thread_index in range(self.NUM_THREADS):
            thread = Thread(target=self.scrape_department_queue, args=())
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()

        return self.new_records
    #########
    # Merging
    #########

    def name_matches(self, person, name):
        names = name.split()
        for divider in range(1, len(names)):
            first_name = ' '.join(names[:divider])
            last_name = ' '.join(names[divider:])
            if person.get('first_name') == first_name and person.get('last_name') == last_name:
                return True
        return False

    def classify_image(self, image_url):
        if image_url is None:
            return 0
        substrings = (
            '/styles/thumbnail',
            '/styles/people_thumbnail',
            '/styles/medium',
            '/styles/people_page',
            'som.yale.edu',
            'medicine.yale.edu',
        )
        for i, substring in enumerate(substrings):
            if substring in image_url:
                return i + 2
        return 1

    def merge_one(self, person, entry):
        if person.get('school_code') != 'YC' and entry.get('image'):
            if person.get('image'):
                # If we have an image already, we should only replace it if the new one is higher quality.
                current_class = self.classify_image(person['image'])
                new_class = self.classify_image(entry['image'])
                if new_class > current_class:
                    person['image'] = entry['image']
            else:
                person['image'] = entry['image']

        new_fields = (
            'cv', 'address', 'email', 'profile', 'website',
            'title', 'suffix', 'education', 'fax',
        )
        for field in new_fields:
            if entry.get(field) and (not person.get(field) or len(person[field]) < len(entry[field])):
                person[field] = entry[field]
        # Fields that we should use if they're found, but not override existing,
        # as departmental data may be lower quality
        fallback_fields = (
            'phone',
        )
        for field in fallback_fields:
            if entry.get(field) and not person.get(field):
                person[field] = entry[field]
        return person

    def merge(self, current_people):
        people = current_people
        emails = {person['email']: i for i, person in enumerate(people) if person.get('email')}

        for record in self.new_records:
            person_i = None
            if record.get('email'):
                person_i = emails.get(record['email'])
            if not person_i:
                matches_found = 0
                latest_person_i = None
                for i, person in enumerate(people):
                    if self.name_matches(person, record['name']):
                        matches_found += 1
                        latest_person_i = i
                # If we find one match, excellent.
                # But if we find more than one, there are multiple people with this name, and unless
                # we can establish which one to choose, we run the risk of matching with the wrong person,
                # so in this case we'll skip this record.
                if matches_found <= 1:
                    person_i = latest_person_i
                else:
                    logger.info('Found multiple name matches, skipping.')

            # Add in data if we found a match
            if person_i:
                logger.info('Matched ' + record['name'] + ' to existing person.')
                people[person_i] = self.merge_one(people[person_i], record)
            else:
                logger.info('Could not match department record to person:')
                logger.info(record)

        return people
