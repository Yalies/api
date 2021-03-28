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
            self.cache.set(cache_key, self.new_records)
            return self.new_records

    def merge(self, current_people):
        """
        Given list of people from previous sources, merge in newly scraped people.
        :param current_people: list of people scraped from previous sources.
        :param new_records: list of new people scraped from this source.
        """
        return current_people + self.new_records
