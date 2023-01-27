from .adapter import Adapter
from app import logger

import requests
import hashlib
from bs4.element import Tag, NavigableString
import re
import logging


class Default(Adapter):
    FUSED_ADDRESS_ROOM_NUMBER_RE = re.compile(r' +Rooms? ([a-zA-Z0-9]{2,}( & )?)+$')

    def get_url(self, path, department_url):
        if path.startswith('/'):
            return department_url + path
        return path

    def get_cards(self, parent, department):
        cards = []
        selector = department.get('cards_selector')
        if selector is not None:
            cards = parent.select(selector)
            if cards is not None:
                return cards
        return parent.select('.view-people tbody tr, .view-people .views-row, .view-people-type tr')

    def get_body(self, parent):
        # Latter is used only on Art History website
        return parent.select_one('#section-content') or parent.select_one('main div.main.columns')

    def extract_image(self, parent, image_replacements, ignored_images):
        img = parent.select_one('.user-picture img, .views-field-field-user-profile-picture img, .field-name-field-user-profile-picture img, .field-name-field-user-image img')
        if img is None:
            return None
        src = img['src']
        src = src.split('?')[0]
        if image_replacements is not None:
            for pair in image_replacements:
                src = src.replace(*pair)
        if ignored_images is not None:
            image_r = requests.get(src, stream=True)
            image_r.raw.decode_content = True
            image_hash = hashlib.md5(image_r.content).hexdigest()
            if image_hash in ignored_images:
                logger.info('Ignoring image with hash ' + image_hash)
                return None
        return src

    def get_field(self, parent, field_name):
        """
        Find field with a given name, or one of a list of names.
        :param parent: BeautifulSoup element to search within.
        :param field_name: name to find, or a list of possible names to search for.
        """
        if isinstance(field_name, list):
            for option in field_name:
                field = self.get_field(parent, option)
                if field:
                    return field
            return None
        container = (
            parent.select_one('.field-name-field-' + field_name) or
            parent.select_one('.views-field-field-' + field_name)
        )
        if not container:
            return None
        return container.select_one('.field-item') or container


    def extract_field(self, parent, field_name):
        elem = self.get_field(parent, field_name)
        if elem is not None:
            return elem.text.strip().replace('\xa0', ' ')


    def extract_field_url(self, parent, field_name):
        elem = self.get_field(parent, field_name)
        if elem is None:
            return None
        link = elem.find('a')
        if link is None:
            return None
        return link['href'].rstrip('/')

    def scrape_path(self, department, path):
        people = []
        if department.get('paginated'):
            logger.info('Paginating...')
            cards = []
            page = 0
            while True:
                people_page_soup = self.get_soup(department['url'] + path, params={'page': page})

                cards_page = self.get_cards(people_page_soup, department)
                if len(cards_page) == 0:
                    break
                cards += cards_page

                logger.info(f'Page {page} had {len(cards_page)} people.')
                page += 1
        else:
            people_soup = self.get_soup(department['url'] + path)
            cards = self.get_cards(people_soup, department)

        for card in cards:
            username = (
                card.find('a', {'class': 'username'}) or
                card.select_one('.user-picture a') or
                # TODO: make sure there aren't any cards that have no link but do have emails
                card.find('a:not(.views-field-field-lab-enter-year a, .views-field-field-orcid a)') or
                # Applied Math website only
                card.select_one('td.views-field-name a:first-child')
            )
            if username is None:
                # There's no profile link; just get what we can from the card
                person = {}
                person['name'] = card.select_one('.views-field-name-1, .views-field-name').text.strip().rstrip(' -')
                person['image'] = self.extract_image(card, department.get('image_replacements'), department.get('ignored_images'))
                title = card.select_one('.views-field-field-title')
                if title is not None:
                    # Sometimes there's an additional wrapping div, which needs to be
                    # removed to avoid the markup working its way in
                    title_field_content = title.select_one('.field-content')
                    if title_field_content is not None:
                        title = title_field_content
                    title = title.encode_contents().decode()
                    #division = None
                    #if '<br/>' in title:
                    #    title, division = title.split('<br/>')
                    title = title.replace('<br/>', ', ')
                    person['title'] = title.strip()
                    #person['division'] = division.strip()
                person['publications'] = self.extract_field_url(card, 'orcid')
            else:
                person = {
                    'profile': self.get_url(username['href'], department['url'])
                }
                person_soup = self.get_soup(person['profile'])
                body = self.get_body(person_soup)
                if not body:
                    logger.info('Could not find profile page body, skipping this person.')
                    continue
                name_suffix = body.find('h1', {'class': ['title', 'page-title']}).text
                # Clean up duplicate spaces, such as on https://clais.macmillan.yale.edu/people/all
                name_suffix = name_suffix.replace('  ', ' ')
                if ' - In Memoriam' in name_suffix:
                    continue
                if name_suffix == 'Access denied':
                    continue
                person['name'], person['suffix'] = self.split_name_suffix(name_suffix)
                email_elem = self.get_field(body, 'email')
                if email_elem and len(email_elem.select('strong')) > 1:
                    # On Econ page, everything is in email row for some reason
                    children = [
                        child for child in email_elem.children
                        if child and (type(child) is Tag and child.text and child.text.strip())
                            or (type(child) is NavigableString and child.encode('utf-8').strip())
                    ]
                    pairs = {}
                    current_key = None
                    for child in children:
                        tag = child.name
                        if tag in ('strong', 'b') and child.text:
                            link = child.find('a')
                            if link is None:
                                current_key = child.text.rstrip(':')
                            else:
                                pairs[child.text] = link['href']
                        elif tag == 'a':
                            pairs[current_key] = child['href'].replace('mailto:', '')
                            current_key = None
                        elif tag is None:
                            # Plain text
                            pairs[current_key] = child.encode('utf-8').decode().strip()
                            current_key = None
                    person.update({
                        'email': pairs.get('Email'),
                        'website': pairs.get('Personal Website'),
                        'cv': pairs.get('Curriculum Vitae'),
                        'address': pairs.get('Office Address'),
                    })
                    title = body.select_one('.group-header h2')
                    if title is not None:
                        person['title'] = title.text
                    image = body.select_one('.content img')
                    if image is not None:
                        TRAILING_ZEROS_RE = re.compile(r'(_0)*\.')
                        image = TRAILING_ZEROS_RE.sub('.', image['src'])
                        if 'placeholder' not in image:
                            person['image'] = image
                else:
                    person.update({
                        'image': self.extract_image(body, department.get('image_replacements'), department.get('ignored_images')),
                        # department-position used here https://clais.macmillan.yale.edu/people/all
                        'title': self.extract_field(body, ['title', 'department-position']),
                        'status': self.extract_field(body, 'status'),
                        'email': self.extract_field(body, 'email'),
                        'education': self.extract_field(body, 'education'),
                        'website': self.extract_field_url(body, ['website', 'faculty-links']),
                        'address': self.extract_field(body, 'address'),
                        'physical_address': self.extract_field(body, 'office-address'),
                        'phone': self.clean_phone(self.extract_field(body, 'phone')),
                        # Only on astronomy website, apparently
                        'research': self.extract_field(body, ['research', 'field-of-study', 'field-of-interest']),
                        # TODO: this could conflict with office_*
                        'room_number': self.extract_field(body, ['room-number', 'office']),
                        'fax': self.clean_phone(self.extract_field(body, 'fax-number')),
                        'cv': self.extract_field_url(body, ['cv', 'curriculum-vitae']),
                        'publications': self.extract_field_url(body, 'publications'),
                        'orcid': self.extract_field(body, 'orcid'),
                        # On Linguistics website
                        'academia_url': self.extract_field_url(body, 'academia-edu'),
                    })

                    if not person['email']:
                        # Useful on Political Science department:
                        # https://politicalscience.yale.edu/people/bruce-ackerman
                        # TODO: parse that
                        # https://github.com/Yalies/api/issues/70
                        email = body.select_one('a[href^="mailto:"]')
                        if email:
                            person['email'] = email.text

                    # Sometimes, particularly in the S&DS department, the room number will simply be stuck onto the end of the address
                    if person['address'] and not person['room_number']:
                        search = self.FUSED_ADDRESS_ROOM_NUMBER_RE.search(person['address'])
                        if search:
                            person['room_number'] = search.group().strip()
                            start, end = search.span()
                            person['address'] = person['address'][:start].strip(',').strip()

                    if person['education']:
                        person['education'] = '\n'.join([degree.strip() for degree in person['education'].split(';')])

                    # There is no elegance here. Only sleep deprivation and regret.
                    if department['name'] == 'Spanish & Portuguese':
                        # The Spanish and Portuguese website puts educational history in the fax number slot
                        # No I don't know why. Gotta do what we gotta do.
                        person.pop('fax')
                        person['education'] = self.extract_field(body, 'fax-number')

                    #bio = self.extract_field(body, 'bio')
                    #if bio is not None:
                    #    person['bio'] = bio.lstrip('_').strip()

            logger.info('Parsed ' + person['name'])
            people.append(person)
        return people
