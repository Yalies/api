from .adapter import Adapter


class Nursing(Adapter):

    def extract_profile_urls(self, parent, department_url):
        links = parent.select('.view-faculty-directory li.views-row a')
        return [department_url + link['href'] for link in links]


    def scrape_path(self, department, path):
        people = []
        people_soup = self.get_soup(department['url'] + path)

        profile_urls = self.extract_profile_urls(people_soup, department['url'])
        for profile_url in profile_urls:
            person = {
                'profile_url': profile_url,
            }
            person_soup = self.get_soup(profile_url)
            person['name'], person['suffix'] = self.split_name_suffix(person_soup.find('h1', {'id': 'page-title'}).text)
            banner = person_soup.find('div', {'class': 'row-1-banner'})
            image = banner.select_one('div.field-name-field-photo img')
            if image and 'facultyblank.jpg' not in image['src']:
                person['image'] = image['src']

            contact_container = banner.select_one('.field-name-field-person-contact-information .field-item')
            if contact_container:
                contact_elems = contact_container.find_all('p', recursive=False)
                if len(contact_elems):
                    person['title'] = contact_elems.pop(0).text.strip()
                if len(contact_elems):
                    strong = contact_elems[0].find('strong')
                    print(strong)
                    if strong is None or not strong.text.strip():
                        person['room_number'] = contact_elems.pop(0).text.strip()
                for contact_elem in contact_elems:
                    # phone, email, fax list. Usually one element, sometimes in multiple
                    # Multiple example: https://nursing.yale.edu/faculty-research/faculty-directory/samantha-conley-phd-rn-fnp-bc
                    contacts = contact_elems.pop(0).text.strip()
                    for contact in contacts.split('\n'):
                        label, value = contact.split(':')
                        person[label] = value.strip()

            people.append(person)
            print('Parsed ' + person['name'])

        return people
