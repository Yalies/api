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

def extract_field(parent, field_name):
    elem = parent.find('div', {'class': 'field-name-field-' + field_name})
    if elem is not None:
        return elem.text


for department in departments:
    if department.get('paths') is None:
        continue

    for path in department['paths']:
        people_page = requests.get(department['url'] + path).text
        people_soup = BeautifulSoup(people_page, 'html.parser')

        cards = soup.find_all('div', {'class': 'views-row'})
        for card in cards:
            person = {
                'profile_url': department['url'] + card.find('a', {'class': 'username'})['href']
            }
            person_page = requests.get(person['profile_url'])
            person_soup = BeautifulSoup(person_page, 'html.parser')

            body = person_soup.find('div', {'id': 'section-content'})
            name = body.find('h1', {'class': 'title'})
            person.update({
                'name': name.text,
                'status': extract_field(body, 'status'),
                'education': extract_field(body, 'education'),
                'bio': extract_field(body, 'bio'),
            })

