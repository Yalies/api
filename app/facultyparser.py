from bs4 import BeautifulSoup
import requests
import json
import re


"""
html = requests.get('https://www.yale.edu/academics/departments-programs').text
soup = BeautifulSoup(html, 'html.parser')
links = soup.find_all('a', {'class': 'department_item_link'})
departments = [
    {
        'name': link.text,
        'url': link['href'],
    } for link in links
]
print(json.dumps(departments))
"""

with open('res/departments.json', 'r') as f:
    departments = json.load(f)

def get_cards(parent, department):
    selector = department.get('cards_selector', 'div.view-people tr')
    return parent.select(selector)

def extract_image(parent):
    container = parent.find('div', {'class': 'user-picture'})
    if container is None:
        return None
    img = container.find('img')
    if img is None:
        return None
    src = img['src']
    # TODO: is this always the best option? It seems we can also use /medium/ and get a larger image, but only for some departments
    src = src.replace('/thumbnail/', '/people_thumbnail/')
    return src

def get_field(parent, field_name):
    return parent.find('div', {'class': 'field-name-field-' + field_name})

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
            people_page_html = requests.get(
                department['url'] + path,
                params = {'page': page}
            ).text
            people_page_soup = BeautifulSoup(people_page_html, 'html.parser')

            cards_page = get_cards(people_page_soup, department)
            if len(cards_page) == 0:
                break
            cards += cards_page

            print(f'Page {page} had {len(cards_page)} people.')
            page += 1
    else:
        people_html = requests.get(department['url'] + path).text
        people_soup = BeautifulSoup(people_html, 'html.parser')
        cards = get_cards(people_soup, department)

    for card in cards:
        person = {
            'profile_url': department['url'] + card.find('a', {'class': 'username'})['href']
        }
        person_page = requests.get(person['profile_url']).text
        person_soup = BeautifulSoup(person_page, 'html.parser')

        body = person_soup.find('main', {'id': 'section-content'})
        name = body.find('h1', {'class': 'title'})
        person.update({
            'name': name.text.strip(),
            'image': extract_image(body),
            'title': extract_field(body, 'title'),
            'status': extract_field(body, 'status'),
            'email': extract_field(body, 'email'),
            'education': extract_field(body, 'education'),
            'website': extract_field_url(body, 'website'),
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
            links = member_listing.find_all('a', {'class': 'profile-grid-item__link-details'})
    return [department_url_root + link['href'] for link in links]

def split_name_suffix(name_suffix):
    chunks = name_suffix.split(', ', 1)
    if len(chunks) == 1:
        chunks.append(None)
    return chunks


def parse_path_medicine(path, department):
    people = []
    people_html = requests.get(department['url'] + path).text
    people_soup = BeautifulSoup(people_html, 'html.parser')

    profile_urls = medicine_extract_links(people_soup, department['url'])
    for profile_url in profile_urls:
        person = {
            'profile_url': profile_url,
        }
        person_html = requests.get(profile_url)
        person_soup = BeautifulSoup(person_html, 'html.parser')

        name_suffix = person_soup.find('h1', {'class': 'profile-details-header__name'}).text
        person['name'], person['suffix'] = split_name_suffix(name_suffix)
        position = person_soup.find('div', {'class': 'profile-details-header__title'})
        if person is not None:
            person['title'] = position.text
        image = person_soup.find('img', {'class': 'profile-details-thumbnail__image'))
        if image is not None:
            image_uuid = image['src'].split('/')[-1]
            # TODO: consider using smaller images
            person['image'] = 'https://files-profile.medicine.yale.edu/images/' + image_uuid

        contact_list = person_soup.find('ul', {'class': 'profile-general-contact-list'})
        if contact_list is not None:
            rows = contact_list.find_all('div', {'class': 'contact_info'})
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

        people.append(person)


def parse_path(path, department):
    website_type = department.get('website_type')
    if website_type == 'medicine':
        return parse_path_medicine(path, department)
    return parse_path_default(path, department)

def scrape():
    people = []
    for department in departments:
        print('Department: ' + department['name'])
        if department.get('paths') is None:
            print('Skipping department.')
            continue

        for path in department['paths']:
            print('Path: ' + path)
            people += parse_path(path, department)

if __name__ == '__main__':
    scrape()
