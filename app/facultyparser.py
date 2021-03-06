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
            'phone': None,
            'email': extract_field(body, 'email'),
            'education': extract_field(body, 'education'),
            'website': extract_field_url(body, 'website'),
            'bio': None,
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


def parse_path_medicine(path, department):
    return []


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
