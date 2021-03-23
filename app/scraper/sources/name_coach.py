from .source import Source

import yaledirectory


class NameCoach(Source):
    def __init__(self, people_search_session_cookie, csrf_token):
        self.directory = yaledirectory.API(people_search_session_cookie, csrf_token)

    ##########
    # Scraping
    ##########

    def scrape(self, current_people):
        pronunciations = []
        for person in current_people:
            if not person['email']:
                print('No email found, skipping pronunciation search.')
                pronunciations.append(None)
            pronunciation = self.directory.pronounce(person['email'])
            if pronunciation:
                print('Found pronunciation for ' + person['email'] + ': ' + pronunciation.recording_url)
                pronunciations.append({
                    'phonetic_name': pronunciation.phonetic_spelling,
                    'name_recording': pronunciation.recording_url,
                    'pronouns': person.get('pronouns') or pronunciation.pronouns,
                })
            else:
                print('No pronunciation found for ' + person['email'] + '.')
                pronunciations.append(None)
        self.new_people = pronunciations

    def merge(self, current_people):
        """
        Given list of people from previous sources, merge in newly scraped people.
        :param current_people: list of people scraped from previous sources.
        :param new_people: list of new people scraped from this source.
        """
        people = []
        for person, pronunciation in zip(current_people, self.new_people):
            people.append({**person, **pronunciation})
        self.people = people
        return people
