from .adapter import Adapter


class Nursing(Adapter):

    def extract_profile_urls(self, parent, department_url):
        links = parent.select('.view-faculty-directory li.views-row a')
        return [department_url + link['href'] for link in links]

    def clean_string(self, string):
        if string is None:
            return None
        return string.strip().replace('\u200b', '')

    def scrape_path(self, department, path):
        people = []
        people_soup = self.get_soup(department['url'] + path)

        profile_urls = self.extract_profile_urls(people_soup, department['url'])
        for profile_url in profile_urls:
            person = {
                'profile': profile_url,
            }
            person_soup = self.get_soup(profile_url)
            person['name'], person['suffix'] = self.split_name_suffix(person_soup.find('h1', {'id': 'page-title'}).text)
            person['name'] = self.NICKNAME_RE.sub('', person['name'])
            banner = person_soup.find('div', {'class': 'row-1-banner'})
            image = banner.select_one('div.field-name-field-photo img')
            if image and 'facultyblank.jpg' not in image['src']:
                person['image'] = image['src'].split('?')[0]

            contact_container = banner.select_one('.field-name-field-person-contact-information .field-item')
            if contact_container:
                contact_elems = contact_container.find_all('p', recursive=False)
                # First, pop contact data lists at bottom
                # Usually they're in a single element, but sometimes two, such as:
                # https://nursing.yale.edu/faculty-research/faculty-directory/samantha-conley-phd-rn-fnp-bc
                while len(contact_elems):
                    if ':' not in contact_elems[-1].text:
                        break
                    contacts = self.clean_string(contact_elems.pop().text)
                    for contact in contacts.split('\n'):
                        label, value = contact.split(':')
                        label = self.clean_string(label)
                        value = self.clean_string(value)
                        if label in ('phone', 'fax'):
                            value = self.clean_phone(value)
                        person[label] = value

                if len(contact_elems):
                    strong = contact_elems[-1].find('strong')
                    if not strong or not self.clean_string(strong.text):
                        person['room_number'] = self.clean_string(contact_elems.pop().text)

                if len(contact_elems):
                    person['title'] = '; '.join([self.clean_string(elem.text) for elem in contact_elems])

            people.append(person)
            print('Parsed ' + person['name'])

        return people
