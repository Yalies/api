from .source import Source

from app import app, db, celery
from app.models import Group, Person, leaderships

import requests
from bs4 import BeautifulSoup, Tag, NavigableString

DEBUG = False
ROOT = 'https://yaleconnect.yale.edu'


class YaleConnect(Source):
    def __init__(self, cache, cookie):
        super().__init__(cache)
        self.cookie = cookie

    ##########
    # Scraping
    ##########

    def get_soup(self, url):
        r = requests.get(
            url,
            headers={'Cookie': self.cookie}
        )
        return BeautifulSoup(r.text, 'html5lib')

    def clean_value(self, value):
        if isinstance(value, str):
            value = value.replace('\u2018', '\'')
            value = value.replace('\u2019', '\'')
            value = value.replace('\u201c', '"')
            value = value.replace('\u201d', '"')
            value = value.replace('\u00a0', ' ')
            value = value.replace('\u2022\t', '- ')
            value = value.replace('\u200b', '')
            return value
        return value

    def scrape(self, current_people):
        # Store people into database
        logging.info('Reading groups list.')
        groups_soup = self.get_soup(
            ROOT + ('/club_signup' if DEBUG else '/club_signup?view=all')
        ).find('div', {'class': 'content-cont'})
        rows = groups_soup.find('ul', {'class': 'list-group'}).find_all('li', {'class': 'list-group-item'})
        # Remove header

        rows.pop(0)
        group_ids = set()
        groups = []
        for row in rows:
            header = row.find('h2', {'class': 'media-heading'})
            a = header.find('a')
            url = a['href']
            try:
                group_id = int(url.replace(ROOT + '/student_community?club_id=', ''))
            except Exception:
                print('Malformed URL. Header content:')
                print(header)
                continue
            name = a.text.strip()
            if group_id in group_ids:
                logging.info(f'Already tracking {name}.')
                continue
            logo = row.find('img')['src']
            if 'Default_Group_Logo' in logo or 'default_club_logo' in logo:
                logo = None
            else:
                logo = ROOT + logo
            groups.append({
                'id': group_id,
                'name': name,
                'logo': logo,
                'mission': '',
                'goals': '',
                'benefits': '',
                'leaders': [],
            })
            group_ids.add(group_id)

        logging.info(groups)

        for i in range(len(groups)):
            group_id = groups[i]['id']
            logging.info('Parsing ' + groups[i]['name'])
            about_soup = self.get_soup(f'{ROOT}/ajax_group_page_about?ax=1&club_id={group_id}').find('div', {'class': 'card-block'})
            current_header = None
            current_contact_property = None
            for child in about_soup.children:
                if child.name == 'h3':
                    current_header = child.text
                else:
                    if current_header == 'GENERAL':
                        if child.name == 'div':
                            text = child.text.strip()
                            if not text:
                                continue
                            prop, value = text.split(': ', 1)
                            prop = prop.lower().replace(' ', '_')
                            prop = {
                                'group_type': 'type',
                            }.get(prop, prop)
                            groups[i][prop] = value
                    elif current_header in ('MISSION', 'MEMBERSHIP BENEFITS', 'GOALS'):
                        if child.name == 'p':
                            prop = current_header.lower().replace(' ', '_')
                            prop = {
                                'membership_benefits': 'benefits',
                            }.get(prop, prop)
                            content = child.find_all(text=True, recursive=False)
                            text = '\n'.join([line.strip() for line in content])
                            groups[i][prop] = (groups[i][prop] + '\n' + text).strip()
                    elif current_header == 'CONSTITUTION':
                        if child.name == 'p':
                            groups[i]['constitution'] = ROOT + child.find('a')['href']
                    elif current_header == 'CONTACT INFO':
                        if isinstance(child, Tag) and child.name == 'span' and child.get('class') is not None and 'mdi' in child['class']:
                            current_contact_property = child['class'][1].replace('mdi-', '')
                        else:
                            if isinstance(child, Tag):
                                text = child.text.strip()
                            else:
                                text = str(child).strip()
                            if text and current_contact_property:
                                if current_contact_property == 'email':
                                    groups[i]['email'] = text
                                elif current_contact_property in ('marker', 'map-marker'):
                                    groups[i]['address'] = '\n'.join([line.strip() for line in text.split('\n')])
                                elif current_contact_property == 'earth':
                                    groups[i]['website'] = text
                                elif current_contact_property == 'cellphone':
                                    groups[i]['phone'] = ''.join([char for char in text if text.isdigit()])
                                else:
                                    logging.info(f'Saw unrecognized contact property {current_contact_property} with value {text}.')
                    elif current_header == 'OFFICERS':
                        if child.name == 'img':
                            leader = {}
                            leader['name'] = child['alt'].replace('Profile image for ', '')
                            ajax_path = child['onclick'].split('\'')[1]
                            leader['id'] = int(ajax_path.split('=')[-1])
                            profile_soup = self.get_soup(ROOT + ajax_path)
                            email_li = profile_soup.find('li', {'class': 'mdi-email'})
                            if email_li:
                                leader['email'] = email_li.find('a')['href'].replace('mailto:', '')
                            groups[i]['leaders'].append(leader)
                    elif current_header is None:
                        pass
                    else:
                        logging.info(f'Encountered unknown About header {current_header}.')

        self.new_records = groups
        return self.new_records

    def merge(self, current_people):
        logging.info('Inserting new data.')
        db.session.query(leaderships).delete()
        Group.query.delete()
        for group_dict in self.new_records:
            leaders = group_dict.pop('leaders', [])
            group_dict = {prop: self.clean_value(value) for prop, value in group_dict.items() if value}
            group = Group(**group_dict)
            db.session.add(group)
            group.leaders[:] = []
            # Remove empty values
            for leader in leaders:
                if not leader.get('email'):
                    logging.warning('Leader without email found:')
                    logging.warning(str(leader))
                    continue
                person = Person.query.filter_by(email=leader['email']).first()
                if person:
                    group.leaders.append(person)
        db.session.commit()
        logging.info('Done.')
        return current_people

