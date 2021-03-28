from .source import Source

import yaledirectory
from threading import Thread


class NameCoach(Source):
    def __init__(self, cache, people_search_session_cookie, csrf_token):
        super().__init__(cache)
        self.directory = yaledirectory.API(people_search_session_cookie, csrf_token)

    ##########
    # Scraping
    ##########

    PAGE_SIZE = 1000

    def scrape_range(self, current_people, begin, end):
        for index in range(begin, end):
            person = current_people[index]
            if not person.get('email'):
                print('No email found, skipping pronunciation search.')
                continue
            pronunciation = self.directory.pronounce(person['email'])
            if pronunciation:
                print('Found pronunciation for ' + person['email'] + ': ' + pronunciation.recording_url)
                self.new_records[index] = {
                    'phonetic_name': pronunciation.phonetic_spelling,
                    'name_recording': pronunciation.recording_url,
                    'pronouns': person.get('pronouns') or pronunciation.pronouns,
                }
            else:
                print('No pronunciation found for ' + person['email'] + '.')

    def scrape(self, current_people):
        self.new_records = [None] * len(current_people)
        threads = []
        for begin in range(0, len(self.new_records), self.PAGE_SIZE):
            thread = Thread(target=self.scrape_range, args=(current_people, begin, begin + self.PAGE_SIZE))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        return self.new_records

    def merge(self, current_people):
        """
        Given list of people from previous sources, merge in newly scraped people.
        :param current_people: list of people scraped from previous sources.
        :param new_records: list of new people scraped from this source.
        """
        people = []
        for person, pronunciation in zip(current_people, self.new_records):
            if pronunciation:
                person.update(pronunciation)
            people.append(person)
        self.people = people
        return people
