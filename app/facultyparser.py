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


