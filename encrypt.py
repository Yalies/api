#!/usr/bin/env python3

import os
from argparse import ArgumentParser
from cryptography.fernet import Fernet

parser = ArgumentParser(description='Process some integers.')
parser.add_argument('filename', type=str, help='Name of file to encrypt')
parser.add_argument('--key', type=str, default=os.environ.get('FERNET_KEY', Fernet.generate_key()))
args = parser.parse_args()

with open(args.filename, 'r') as f:
    content = f.read()
encoded_content = content.encode()
f = Fernet(args.key.encode())
encrypted_content = f.encrypt(encoded_content)
with open(args.filename + '.fernet', 'wb') as f:
    f.write(encrypted_content)

print('Key:')
print(args.key)
