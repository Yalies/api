from .adapter import Adapter
import requests
from bs4 import BeautifulSoup
import html5lib


class Law(Adapter):
    def get_field(self, parent, field_name):
        return parent.find('li', {'class': field_name})

    def extract_field(self, parent, field_name):
        field = self.get_field(parent, field_name)
        if field is None:
            return None
        return field.text.strip()

    def scrape_path(self, department, path):
        people = []

        people_soup = self.get_soup(department['url'] + path)
        profile_links = people_soup.select('.faculty-result-content h2 a')
        profile_urls = [department['url'] + link['href'] for link in profile_links]
        profile_urls = list(set(profile_urls))

        for profile_url in profile_urls:
            person = {
                'profile': profile_url,
            }
            person_html = requests.get(profile_url).text
            person_soup = BeautifulSoup(person_html, 'html5lib')
            person['name'] = person_soup.find('h1').text.strip()
            title = person_soup.find('p', {'class': 'sub-title'})
            if title:
                person['title'] = title.text
            leave = person_soup.find('p', {'class': 'on-leave'})
            if leave:
                person['leave'] = bool(leave.text.strip())
            contacts = person_soup.select_one('div.faculty-content ul')
            person.update({
                'room_number': self.extract_field(contacts, 'door'),
                'phone': self.clean_phone(self.extract_field(contacts, 'phone')),
                'email': self.extract_field(contacts, 'email'),
            })
            cv = person_soup.select_one('div.faculty-content li.document a')
            if cv:
                person['cv'] = cv['href']

            people.append(person)
            print('Parsed ' + person['name'])
        return people