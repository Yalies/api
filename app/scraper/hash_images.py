import requests
import hashlib

def hashimg(url):
	r = requests.get(url.split('?')[0], stream=True)
	r.raw.decode_content = True
	return hashlib.md5(r.content).hexdigest()

with open('/tmp/imagelinks', 'r') as f:
	imagelinks = f.read().split()

hashes = [hashimg(l) for l in imagelinks]
unique_hashes = list(set(hashes))
print('\n'.join(unique_hashes))
