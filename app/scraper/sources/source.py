import re

class Source:
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
        return phone

    ###############
    # Scraping flow
    ###############

    def scrape(self):
        """
        Read all people from this source.
        """
        raise NotImplementedError

    def merge(self, current_people, new_people):
        """
        Given list of people from previous sources, merge in newly scraped people.
        :param current_people: list of people scraped from previous sources.
        :param new_people: list of new people scraped from this source.
        """
        return current_people + new_people

    def integrate(self, current_people):
        """
        Run scraper and integrate results into existing list of people.
        :param people: list of existing people from previous sources.
        :return: list with new records integrated.
        """
        new_people = self.scrape()
        return self.merge(current_people, new_people)
