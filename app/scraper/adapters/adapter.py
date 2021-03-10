import requests
from bs4 import BeautifulSoup
import re



class Adapter:
    NICKNAME_RE = re.compile(r' "[A-Za-z\. ]+"')

    ##############
    # Util methods
    ##############

    def get_soup(self, url, **kwargs):
        #print('Souping URL: ' + url)
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

    # TODO: deduplicate
    def clean_phone(self, phone):
        if not phone:
            return phone
        if type(phone) == int:
            phone = str(phone)
        COUNTRY_CODE_RE = re.compile('^\+1?[ \u00a0]')
        phone = COUNTRY_CODE_RE.sub('', phone)
        DISALLOWED_CHARACTERS_RE = re.compile(r'[A-Za-z\(\) \-\.]')
        phone = DISALLOWED_CHARACTERS_RE.sub('', phone)
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
            print('Skipping department.')
            return []

        people = []
        for path in paths:
            print('Scraping path: ' + path)
            people += self.scrape_path(department, path)
        return people
