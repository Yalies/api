from .adapter import Adapter
from app import logger


class Jackson(Adapter):

    def get_cards(self, parent):
        return parent.find_all('div', {'class': 'page-item-person'})

    def get_field(self, parent, field_name):
        return parent.select_one('.page-item-person-' + field_name)

    def extract_field(self, parent, field_name):
        field = self.get_field(parent, field_name)
        if field is None:
            return None
        return field.text

    def scrape_path(self, department, path):
        people = []

        people_soup = self.get_soup(department['url'] + path)
        # Handle both table styles
        cards = self.get_cards(people_soup)
        logger.info(f'Found {len(cards)} people.')

        for card in cards:
            person = {
                'name': self.extract_field(card, 'name').strip(),
                'title': self.extract_field(card, 'bio-title'),
            }
            image = card.select_one('.page-item-image img')
            if image:
                person['image'] = image['src']
            email = card.select_one('.page-item-bio-link a[href^="mailto:"]')
            if email:
                person['email'] = email['href'].replace('mailto:', '')
            phone = card.select_one('.page-item-bio-link a[href^="tel:"]')
            if phone:
                person['phone'] = self.clean_phone(phone['href'].replace('tel:', ''))

            profile_link = card.select_one('.page-item-person-bio-link a.more')
            if profile_link:
                person['profile'] = profile_link['href']
                # TODO: parse bio and anything else useful from profile pages
                # It doesn't seem like there's any other useful information in profiles though
                #person_soup = self.get_soup(profile_url)
            people.append(person)
            logger.info('Parsed ' + person['name'])
        return people
