from .adapter import Adapter
from app import logger


class Medicine(Adapter):

    def extract_links(self, parent, department_url):
        department_url_root = self.get_url_root(department_url)
        links = (
            parent.select('section.generic-anchored-list a.hyperlink') or
            parent.select('div.profile-grid div.profile-grid-item__name-container a.profile-grid-item__link-details') or
            # A list like https://medicine.yale.edu/bbs/people/plantmolbio
            parent.select('.generic-content__table-wrapper a')
        )
        return [department_url_root + link['href'] for link in links]


    def scrape_path(self, department, path):
        people = []
        people_soup = self.get_soup(department['url'] + path)

        profile_urls = self.extract_links(people_soup, department['url'])
        logger.info(f'Found {len(profile_urls)} profile URLs.')
        for profile_url in profile_urls:
            person = {
                'profile': profile_url,
            }
            person_soup = self.get_soup(profile_url)

            name_suffix = person_soup.find('h1', {'class': 'profile-details-header__name'})
            if name_suffix is None:
                logger.info('Empty page, skipping.')
                continue
            person['name'], person['suffix'] = self.split_name_suffix(name_suffix.text)
            title = person_soup.find('div', {'class': 'profile-details-header__title'})
            if title:
                person['title'] = title.text
            image = person_soup.find('img', {'class': 'profile-details-thumbnail__image'})
            if image:
                image_uuid = image['src'].split('/')[-1]
                # TODO: consider using smaller images
                person['image'] = 'https://files-profile.medicine.yale.edu/images/' + image_uuid

            contact_list = person_soup.find('ul', {'class': 'profile-general-contact-list'})
            if contact_list:
                rows = contact_list.find_all('div', {'class': 'contact-info'})
                contacts = {}
                for row in rows:
                    label = row.find('span', {'class': 'contact-info__label'}).text
                    content = row.find('div', {'class': 'contact-info__content'}).text.strip()
                    contacts[label] = content
                person.update({
                    'phone': self.clean_phone(contacts.get('Office')),
                    'fax': self.clean_phone(contacts.get('Fax')),
                    # TODO: these are really specific and seem to usually be the same as Office and Fax
                    #'appointment_phone': clean_phone(contacts.get('Appt')),
                    #'clinic_fax': clean_phone(contacts.get('Clinic Fax')),
                    'email': contacts.get('Email'),
                })

            mailing_address = person_soup.find('div', {'class': 'profile-mailing-address'})
            if mailing_address:
                person['mailing_address'] = '\n'.join([p.text for p in mailing_address.find_all('p')])

            website = person_soup.select_one('.profile-details-sidebar__lab-website-container a.button')
            if website:
                person['website'] = website['href']

            cv = person_soup.select_one('.profile-details-sidebar__cv-container a.button')
            if cv:
                person['cv'] = cv['href']

            #bio = person_soup.find('div', {'class': 'profile-details-biography-tab__biography'})
            #if bio:
            #    person['bio'] = bio.text.strip()

            logger.info('Parsed ' + person['name'])
            people.append(person)
        return people

