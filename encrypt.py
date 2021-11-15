#!/usr/bin/env python3

import os
from argparse import ArgumentParser
from bs4 import BeautifulSoup
import json
from cryptography.fernet import Fernet

parser = ArgumentParser(description='Process some integers.')
parser.add_argument('filename', type=str, help='Name of file to encrypt')
parser.add_argument('--key', type=str, default=os.environ.get('FERNET_KEY', Fernet.generate_key()))
args = parser.parse_args()

# TODO: don't duplicate from FaceBook class
def clean_year(year):
    year = year.lstrip('\'')
    if not year:
        return None
    return 2000 + int(year)

def get_tree(html):
    print('Building tree.')
    tree = BeautifulSoup(html, 'html.parser')
    print('Done building tree.')
    return tree

def get_containers(tree):
    return tree.find_all('div', {'class': 'student_container'})

with open(args.filename, 'r') as f:
    html = f.read()

years = {}

print(f'Reading years from page.')
tree = get_tree(html)
containers = get_containers(tree)

for container in containers:
    year = clean_year(container.find('div', {'class': 'student_year'}).text)
    info = container.find_all('div', {'class': 'student_info'})
    try:
        email = info[1].find('a').text
    except AttributeError:
        continue
    years[email] = year

content = json.dumps(years)
print(content)
encoded_content = content.encode()
f = Fernet(args.key.encode())
encrypted_content = f.encrypt(encoded_content)
with open(args.filename.replace('.html', '.json') + '.fernet', 'wb') as f:
    f.write(encrypted_content)

print('Key:')
print(args.key)
