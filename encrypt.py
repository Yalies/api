from cryptography.fernet import Fernet

key = Fernet.generate_key()

with open('pre2020.html', 'r') as f:
    page = f.read()
encoded_page = page.encode()
f = Fernet(key)
encrypted_page = f.encrypt(encoded_page)
with open('pre2020.html.fernet', 'wb') as f:
    f.write(encrypted_page)

print('Key:')
print(key.decode())
