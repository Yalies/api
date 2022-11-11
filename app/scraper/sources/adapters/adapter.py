from app import logger
import requests
from bs4 import BeautifulSoup
import re


class Adapter:

    #########################
    # Regex for cleaning data
    #########################

    NICKNAME_RE = re.compile(r' "[A-Za-z\. ]+"')

    PHONE_COUNTRY_CODE_RE = re.compile('^\+1?[ \u00a0]')
    PHONE_DISALLOWED_CHARACTERS_RE = re.compile(r'[A-Za-z\(\) \-\.]')

    ##############
    # Util methods
    ##############

    def get_soup(self, url, **kwargs):
        #logger.info('Souping URL: ' + url)
        html = requests.get(url, **kwargs).text
        return BeautifulSoup(html, 'html.parser')

    def split_name_suffix(self, name_suffix):
        chunks = name_suffix.split(',', 1)
        chunks = [chunk.strip() for chunk in chunks]
        if len(chunks) == 1:
            chunks.append(None)
        elif chunks[1].startswith('\u2018'):
            # If the suffix appears to be a graduation year
            chunks[1] = None
        return chunks

    def clean_image(self, image):
        if image is None:
            return None
        return image.split('?')[0]

    # TODO: deduplicate
    def clean_phone(self, phone):
        if not phone:
            return phone
        if type(phone) == int:
            phone = str(phone)
        phone = self.PHONE_COUNTRY_CODE_RE.sub('', phone)
        phone = self.PHONE_DISALLOWED_CHARACTERS_RE.sub('', phone)
        if ',' in phone:
            phone = phone.split(',')[0]
        if len(phone) == 7:
            phone = '203' + phone
        return phone

    def get_url_root(self, url):
        return '/'.join(url.split('/')[:3])


    ##############
    # Scraper flow
    ##############

    def scrape_path(self, department, path):
        raise NotImplementedError

    def scrape(self, department):
        paths = department.get('paths')
        if paths is None:
            logger.info('Skipping department.')
            return []

        people = []
        for path in paths:
            logger.info('Scraping path: ' + path)
            people += self.scrape_path(department, path)
        return people
