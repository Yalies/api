from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
import requests
import json
import re
import hashlib


def get_soup(url, **kwargs):
    #print('Souping URL: ' + url)
    html = requests.get(url, **kwargs).text
    return BeautifulSoup(html, 'html.parser')


def get_cards(parent, department):
    cards = []
    selector = department.get('cards_selector')
    if selector is not None:
        cards = parent.select(selector)
        if cards is not None:
            return cards
    return parent.select('.view-people tbody tr, .view-people .views-row')


def extract_image(parent, image_replacements, ignored_images):
    img = parent.select_one('.user-picture img, .views-field-field-user-profile-picture img, .field-name-field-user-profile-picture img')
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
            print('Ignoring image with hash ' + image_hash)
            return None
    return src


def get_field(parent, field_name):
    container = (
        parent.select_one('.field-name-field-' + field_name) or
        parent.select_one('.views-field-field-' + field_name)
    )
    if not container:
        return None
    return container.select_one('.field-item') or container


def extract_field(parent, field_name):
    elem = get_field(parent, field_name)
    if elem is not None:
        return elem.text.strip().replace('\xa0', ' ')


def extract_field_url(parent, field_name):
    elem = get_field(parent, field_name)
    if elem is None:
        return None
    link = elem.find('a')
    if link is None:
        return None
    return link['href'].rstrip('/')


def split_name_suffix(name_suffix):
    chunks = name_suffix.split(',', 1)
    chunks = [chunk.strip() for chunk in chunks]
    if len(chunks) == 1:
        chunks.append(None)
    elif chunks[1].startswith('\u2018'):
        # If the suffix appears to be a graduation year
        chunks[1] = None
    return chunks


# TODO: deduplicate
def clean_phone(phone):
    if not phone:
        return phone
    if type(phone) == int:
        phone = str(phone)
    COUNTRY_CODE_RE = re.compile('^\+1? ')
    phone = COUNTRY_CODE_RE.sub('', phone)
    DISALLOWED_CHARACTERS_RE = re.compile(r'[A-Za-z\(\) \-\.]')
    phone = DISALLOWED_CHARACTERS_RE.sub('', phone)
    return phone


def parse_path_default(path, department):
    people = []
    if department.get('paginated'):
        print('Paginating...')
        cards = []
        page = 0
        while True:
            people_page_soup = get_soup(department['url'] + path, params={'page': page})

            cards_page = get_cards(people_page_soup, department)
            if len(cards_page) == 0:
                break
            cards += cards_page

            print(f'Page {page} had {len(cards_page)} people.')
            page += 1
    else:
        people_soup = get_soup(department['url'] + path)
        cards = get_cards(people_soup, department)

    for card in cards:
        username = (
            card.find('a', {'class': 'username'}) or
            card.select_one('.user-picture a') or
            # TODO: make sure there aren't any cards that have no link but do have emails
            card.find('a:not(.views-field-field-lab-enter-year a, .views-field-field-orcid a)')
        )
        if username is None:
            # There's no profile link; just get what we can from the card
            person = {}
            person['name'] = card.select_one('.views-field-name-1, .views-field-name').text.strip().rstrip(' -')
            person['image'] = extract_image(card, department.get('image_replacements'), department.get('ignored_images'))
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
            orcid = extract_field_url(card, 'orcid')
            if orcid is not None:
                person['orcid'] = orcid.replace('http://orcid.org/', '').replace('https://orcid.org/', '')
        else:
            person = {
                'profile_url': department['url'] + username['href']
            }
            person_soup = get_soup(person['profile_url'])
            body = person_soup.select_one('#section-content')
            if not body:
                print('Could not find profile page body, skipping this person.')
                continue
            name_suffix = body.find('h1', {'class': ['title', 'page-title']}).text
            if ' - In Memoriam' in name_suffix:
                continue
            if name_suffix == 'Access denied':
                continue
            person['name'], person['suffix'] = split_name_suffix(name_suffix)
            email_elem = get_field(body, 'email')
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
                    'image': extract_image(body, department.get('image_replacements'), department.get('ignored_images')),
                    'title': extract_field(body, 'title'),
                    'status': extract_field(body, 'status'),
                    'email': extract_field(body, 'email'),
                    'education': extract_field(body, 'education'),
                    'website': extract_field_url(body, 'website') or extract_field_url(body, 'faculty-links'),
                    'address': extract_field(body, 'address'),
                    'physical_address': extract_field(body, 'office-address'),
                    'phone': clean_phone(extract_field(body, 'phone')),
                    # Only on astronomy website, apparently
                    'research': extract_field(body, 'research'),
                    # TODO: this could conflict with office_*
                    'room_number': extract_field(body, 'room-number'),
                    'fax': clean_phone(extract_field(body, 'fax-number')),
                    'orcid': extract_field(body, 'orcid'),
                })
                bio = extract_field(body, 'bio')
                if bio is not None:
                    person['bio'] = bio.lstrip('_').lstrip()

        print('Parsed ' + person['name'])
        people.append(person)
    return people

def get_url_root(url):
    return '/'.join(url.split('/')[:3])

def medicine_extract_links(parent, department_url):
    department_url_root = get_url_root(department_url)
    links = (
        parent.select('section.generic-anchored-list a.hyperlink') or
        parent.select('div.profile-grid div.profile-grid-item__name-container a.profile-grid-item__link-details') or
        # A list like https://medicine.yale.edu/bbs/people/plantmolbio
        parent.select('.generic-content__table-wrapper a')
    )
    return [department_url_root + link['href'] for link in links]


def parse_path_medicine(path, department):
    people = []
    people_soup = get_soup(department['url'] + path)

    profile_urls = medicine_extract_links(people_soup, department['url'])
    print(f'Found {len(profile_urls)} profile URLs.')
    for profile_url in profile_urls:
        person = {
            'profile_url': profile_url,
        }
        person_soup = get_soup(profile_url)

        name_suffix = person_soup.find('h1', {'class': 'profile-details-header__name'})
        if name_suffix is None:
            print('Empty page, skipping.')
            continue
        person['name'], person['suffix'] = split_name_suffix(name_suffix.text)
        title = person_soup.find('div', {'class': 'profile-details-header__title'})
        if title is not None:
            person['title'] = title.text
        image = person_soup.find('img', {'class': 'profile-details-thumbnail__image'})
        if image is not None:
            image_uuid = image['src'].split('/')[-1]
            # TODO: consider using smaller images
            person['image'] = 'https://files-profile.medicine.yale.edu/images/' + image_uuid

        contact_list = person_soup.find('ul', {'class': 'profile-general-contact-list'})
        if contact_list is not None:
            rows = contact_list.find_all('div', {'class': 'contact-info'})
            contacts = {}
            for row in rows:
                label = row.find('span', {'class': 'contact-info__label'}).text
                content = row.find('div', {'class': 'contact-info__content'}).text.strip()
                contacts[label] = content
            person.update({
                'phone': clean_phone(contacts.get('Office')),
                'fax': clean_phone(contacts.get('Fax')),
                # TODO: these are really specific and seem to usually be the same as Office and Fax
                #'appointment_phone': clean_phone(contacts.get('Appt')),
                #'clinic_fax': clean_phone(contacts.get('Clinic Fax')),
                'email': contacts.get('Email'),
            })

        mailing_address = person_soup.find('div', {'class': 'profile-mailing-address'})
        if mailing_address is not None:
            person['mailing_address'] = '\n'.join([p.text for p in mailing_address.find_all('p')])

        website = person_soup.select_one('.profile-details-sidebar__lab-website-container a.button')
        if website is not None:
            person['website'] = website['href']

        bio = person_soup.find('div', {'class': 'profile-details-biography-tab__biography'})
        if bio is not None:
            person['bio'] = bio.text.strip()

        print('Parsed ' + person['name'])
        people.append(person)
    return people


def parse_path_architecture(path, department):
    people = []

    page = 1
    profile_urls = []
    while True:
        people_page_soup = get_soup(department['url'] + path, params={'page': page})
        links_page = people_page_soup.select('div.faculty-member-thumbnail a')
        if len(links_page) == 0:
            break
        print(f'Found {len(links_page)} people on page {page}.')
        profile_urls += [department['url'] + link['href'] for link in links_page]
        page += 1

    for profile_url in profile_urls:
        person = {
            'profile_url': profile_url,
        }
        person_soup = get_soup(profile_url)
        image = person_soup.select_one('.faculty-show__top-area img')
        if image is not None:
            image = image['srcset'].split('?')[0].replace('/convert', '')
            person['image'] = image
        person['name'] = person_soup.find('h1', {'class': 'h2'}).text
        title = person_soup.find('div', {'class': 'h2'})
        if title:
            person['title'] = title.text
        # TODO: parse bio and education as well
        print('Parsing ' + person['name'])
        people.append(person)
    return people


def parse_path_seas(path, department):
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

    print(profile_urls)

    return people


def parse_path(path, department):
    website_type = department.get('website_type')
    if website_type == 'medicine':
        return parse_path_medicine(path, department)
    if website_type == 'architecture':
        return parse_path_architecture(path, department)
    if website_type == 'seas':
        return parse_path_seas(path, department)
    return parse_path_default(path, department)

def scrape():
    people = []
    with open('res/departments.json', 'r') as f:
        departments = json.load(f)
    enabled_departments = [department for department in departments if department.get('enabled')]
    # If any departments have been marked enabled, filter to just them
    if enabled_departments:
        departments = enabled_departments
    for department in departments:
        print('Department: ' + department['name'])
        if department.get('paths') is None:
            print('Skipping department.')
            continue

        for path in department['paths']:
            print('Path: ' + path)
            people += parse_path(path, department)
    return people

if __name__ == '__main__':
    people = scrape()
    with open('/tmp/people.json', 'w') as f:
        json.dump(people, f)
