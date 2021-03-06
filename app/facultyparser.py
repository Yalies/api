from bs4 import BeautifulSoup
import requests
import json


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

people = []

def extract_image(parent):
    container = person_soup.find('div', {'class': 'user-picture'})
    if container is None:
        return None
    img = container.find('img')
    if img is None:
        return None
    src = img['src']
    # TODO: is this always the best option? It seems we can also use /medium/ and get a larger image, but only for some departments
    src = src.replace('/thumbnail/', '/people_thumbnail/')
    return src

def extract_field(parent, field_name):
    elem = parent.find('div', {'class': 'field-name-field-' + field_name})
    if elem is not None:
        return elem.text.strip().replace('\xa0', ' ')


for department in departments:
    print('Department: ' + department['name'])
    if department.get('paths') is None:
        print('Skipping department.')
        continue

    for path in department['paths']:
        people_page = requests.get(department['url'] + path).text
        people_soup = BeautifulSoup(people_page, 'html.parser')

        cards = people_soup.find_all('div', {'class': 'views-row'})
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
                'bio': None,
            })
            bio = extract_field(body, 'bio')
            if bio is not None:
                person['bio'] = bio.lstrip('_').lstrip()

            print('Parsed ' + person['name'])
            people.append(person)

print(people)
