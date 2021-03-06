from bs4 import BeautifulSoup
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
        image_hash = hashlib.md5(r.content)
        if image_hash in ignored_images:
            return None
    return src


def get_field(parent, field_name):
    container = parent.find('div', {'class': 'field-name-field-' + field_name})
    if not container:
        return None
    return container.find('div', {'class': 'field-item'})


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
    return chunks


# TODO: deduplicate
def clean_phone(phone):
    if not phone:
        return phone
    if type(phone) == int:
        phone = str(phone)
    COUNTRY_CODE_RE = re.compile('^\+1? ')
    phone = COUNTRY_CODE_RE.sub('', phone)
    DISALLOWED_CHARACTERS_RE = re.compile(r'[\(\) \-]')
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
        username = card.find('a', {'class': 'username'})
        if username is None:
            # TODO: make sure there aren't any cards that have no link but do have emails
            username = card.find('a')
        if username is None:
            # There's no profile link; just get what we can from the card
            person = {}
            person['name'] = card.select_one('.views-field-name-1').text.strip()
            person['image'] = extract_image(card, department.get('image_replacements'), department.get('ignored_images'))
            title = card.select_one('.views-field-field-title')

            # Sometimes there's an additional wrapping div, which needs to be
            # removed to avoid the markup working its way in
            title_field_content = title.select_one('.field-content')
            if title_field_content is not None:
                title = title_field_content

            if title is not None:
                title = title.encode_contents().decode()
                #division = None
                #if '<br/>' in title:
                #    title, division = title.split('<br/>')
                title = title.replace('<br/>', ', ')
                person['title'] = title.strip()
                #person['division'] = division.strip()
        else:
            person = {
                'profile_url': department['url'] + username['href']
            }
            person_soup = get_soup(person['profile_url'])
            body = person_soup.select_one('#section-content')
            name_suffix = body.find('h1', {'class': ['title', 'page-title']}).text
            if ' - In Memoriam' in name_suffix:
                continue
            person['name'], person['suffix'] = split_name_suffix(name_suffix)
            person.update({
                'image': extract_image(body, department.get('image_replacements'), department.get('ignored_images')),
                'title': extract_field(body, 'title'),
                'status': extract_field(body, 'status'),
                'email': extract_field(body, 'email'),
                'education': extract_field(body, 'education'),
                'website': extract_field_url(body, 'website') or extract_field_url(body, 'faculty-links'),
                'address': extract_field(body, 'address'),
                'physical_address': extract_field(body, 'office-address'),
            })
            phone = extract_field(body, 'phone')
            if phone is not None:
                person['phone'] = clean_phone(phone)
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
    generic_list = parent.find('section', {'class': 'generic-anchored-list'})
    if generic_list is not None:
        links = generic_list.find_all('a', {'class': 'hyperlink'})
    else:
        member_listing = parent.find('section', {'class': 'organization-member-listing'})
        if member_listing is not None:
            links = member_listing.select('div.profile-grid-item__content-container a.profile-grid-item__link-details')
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
                'phone': contacts.get('Office'),
                'fax': contacts.get('Fax'),
                # TODO: these are really specific and seem to usually be the same as Office and Fax
                #'appointment_phone': contacts.get('Appt'),
                #'clinic_fax': contacts.get('Clinic Fax'),
                'email': contacts.get('Email'),
            })

        mailing_address = person_soup.find('div', {'class': 'profile-mailing-address'})
        if mailing_address is not None:
            person['mailing_address'] = '\n'.join([p.text for p in mailing_address.find_all('p')])

        bio = person_soup.find('div', {'class': 'profile-details-biography-tab__biography'})
        if bio is not None:
            person['bio'] = bio.text.strip()

        print('Parsed ' + person['name'])
        people.append(person)
    return people


def parse_path(path, department):
    website_type = department.get('website_type')
    if website_type == 'medicine':
        return parse_path_medicine(path, department)
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
