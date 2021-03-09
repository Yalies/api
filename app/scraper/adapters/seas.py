from .adapter import Adapter


class Seas(Adapter):

    def extract_field(self, parent, field_name):
        field = parent.select_one('.info-div.person-' + field_name)
        if not field:
            return None
        label = field.find('strong')
        if label:
            label.extract()
        for br in field.find_all('br'):
            br.replace_with('\n')
        # TODO: clean up address cleaning
        SPACE_RE = re.compile(r' {2,}')
        text = field.text
        text = SPACE_RE.sub(' ', text.strip())
        text = '\n'.join([component.strip() for component in text.split('\n')])
        return text

    def scrape_path(self, department, path):
        people = []

        page = 0
        profile_urls = []
        while True:
            people_page_soup = get_soup(department['url'] + path, params={'page': page})
            links_page = people_page_soup.select('.view-faculty-directory .view-content > div .views-field-title .viewmore a:not([title])')
            print(f'Found {len(links_page)} people on page {page}.')
            profile_urls += [department['url'] + link['href'] for link in links_page]
            next_button = people_page_soup.select_one('li.pager-next a')
            if next_button is None:
                break
            page += 1

        for profile_url in profile_urls:
            person = {
                'profile_url': profile_url,
            }
            person_soup = self.get_soup(profile_url)
            body = person_soup.find('article')
            person['name'] = body.find('h1', {'class': 'title'}).text
            # RIP Stan
            if 'In Memoriam' in person['name']:
                continue
            image = body.select_one('.person-image img')
            if image is not None:
                person['image'] = image['src']
            person.update({
                'title': self.extract_field(body, 'dpttext'),
                'room_number': self.extract_field(body, 'office'),
                'address': self.extract_field(body, 'officeadd'),
                'postal_address': self.extract_field(body, 'mailadd'),
                'phone': self.clean_phone(self.extract_field(body, 'phone')),
                'fax': self.clean_phone(self.extract_field(body, 'fax')),
                #'education': extract_field(body, 'degrees'),
            })
            website = person_soup.select_one('.person-image .website a')
            if website is not None:
                person['website'] = website['href']

            people.append(person)
            print('Parsed ' + person['name'])
        return people

