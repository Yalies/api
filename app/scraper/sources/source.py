import re
import json

class Source:
    def __init__(self, cache):
        self.cache = cache

    ###########
    # Utilities
    ###########

    RE_PHONE_COUNTRY_CODE = re.compile(r'^\+1? ')
    RE_PHONE_DISALLOWED_CHARACTERS = re.compile(r'[A-Za-z\(\) \-\.]')

    def clean_phone(self, phone):
        if not phone:
            return phone
        if type(phone) == int:
            phone = str(phone)
        phone = self.RE_PHONE_COUNTRY_CODE.sub('', phone)
        phone = self.RE_PHONE_DISALLOWED_CHARACTERS.sub('', phone)
        if phone in ('1111111111'):
            return None
        return phone

    ###############
    # Scraping flow
    ###############

    new_records = None
    people = None

    def scrape(self, current_people):
        """
        Read all people from this source and store to new_records.
        """
        raise NotImplementedError

    def clean_one(self, person):
        """
        Remove empty properties from person record.
        :param person: single person record.
        """
        return {k: v for k, v in person.items() if v or type(v) == bool}

    def clean(self, people):
        """
        Remove empty properties from a list of people.
        :param person: list of people records.
        """
        return [self.clean_one(person) for person in people]

    def pull(self, current_people):
        """
        Read data from this source, either through cache or by running scraper.
        """
        cache_key = 'scraped_data.' + self.__class__.__name__
        people = self.cache.get(cache_key)

        if people:
            self.new_records = people
            return self.new_records
        else:
            self.scrape(current_people)
            # Strip out empty properties for space efficiency
            self.new_records = self.clean(self.new_records)
            self.cache.set(cache_key, self.new_records)
            return self.new_records

    def merge(self, current_people):
        """
        Given list of people from previous sources, merge in newly scraped people.
        :param current_people: list of people scraped from previous sources.
        """
        return current_people + self.new_records

    def integrate(self, current_people):
        """
        Given list of people from previous sources, merge in newly scraped people and clean up.
        :param current_people: list of people scraped from previous sources.
        """
        people = self.merge(current_people)
        people = self.clean(people)
        return people
