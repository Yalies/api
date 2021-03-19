from .adapter import Adapter
import re


class Environment(Adapter):

    def get_field(self, parent, field_name):
        return parent.select_one('.' + field_name)

    def extract_field(self, parent, field_name):
        field = self.get_field(parent, field_name)
        if field is None:
            return None
        for br in field.find_all('br'):
            br.replace_with('\n')
        return field.text.strip().replace('\n\r\n', '\n')

    def extract_field_url(self, parent, field_name, root=None):
        field = self.get_field(parent, field_name)
        if field is None:
            return None
        if field.name != 'a':
            field = field.find('a')
            if field is None:
                return None
        url = field['href']
        if url is not None and url.startswith('/') and root is not None:
            url = root + url
        return url

    def scrape_path(self, department, path):
        people = []

        people_soup = self.get_soup(department['url'] + path)
        # Handle both table styles
        links = people_soup.select('.row_wrap.listing > a, .primary_body tr a[title]')
        print(f'Found {len(links)} people.')
        profile_urls = [department['url'] + link['href'] for link in links]
        profile_urls = list(set(profile_urls))

        for profile_url in profile_urls:
            person = {
                'profile': profile_url,
            }
            person_soup = self.get_soup(profile_url)
            body = person_soup.find('div', {'class': 'content_wrapper'})
            name = body.find('h1').text.strip()
            # TODO: don't declare this every loop
            name = self.NICKNAME_RE.sub('', name.replace('  ', ' '))
            person['name'] = name
            title = body.select_one('h4 em')
            if title is not None:
                person['title'] = title.text.strip()
            sidebar = body.select_one('.cell.box_it')
            image = sidebar.find('img')
            if image is not None:
                person['image'] = department['url'] + image['src'].split('?')[0]
            person.update({
                'email': self.extract_field(sidebar, 'email'),
                'phone': self.clean_phone(self.extract_field(sidebar, 'tel')),
                'address': self.extract_field(sidebar, 'profile_contact'),
                'cv': self.extract_field_url(body, 'cv', root=department['url']),
            })
            website = sidebar.select_one('.cell_link a')
            if website is not None:
                person['website'] = website['href']

            people.append(person)
            print('Parsed ' + person['name'])
        return people
