import boto3
import botocore
import os
import hashlib


S3_BUCKET_NAME = 'yalestudentphotos'
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.environ.get('S3_SECRET_ACCESS_KEY')
S3_LOCATION = 'https://' + S3_BUCKET_NAME + '.s3.amazonaws.com/'

class ImageUploader:
    def __init__(self):
        self.s3 = boto3.client(
           's3',
           aws_access_key_id=S3_ACCESS_KEY,
           aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        )
        self.image_ids = self.get_image_ids()

    def get_image_ids(self):
        paginator = self.s3.get_paginator('list_objects')
        page_iterator = paginator.paginate(Bucket=S3_BUCKET_NAME)
        image_ids = set()
        for page in page_iterator:
            image_ids.update({int(obj['Key'].rstrip('.jpg')) for obj in page['Contents']})
        return image_ids

    def get_image_filename(self, image_id, person):
        unique_identifier = '-'.join([
            str(image_id),
            person.get('netid', ''),
            str(person.get('upi', '')),
        ])
        image_name = hashlib.md5(unique_identifier.encode()).hexdigest()
        return f'{image_name}.jpg'

    def get_file_url(self, filename):
        return '{}{}'.format(S3_LOCATION, filename)

    def get_image_url(self, image_id, person):
        return self.get_file_url(self.get_image_filename(image_id, person))

    def upload_image(self, image_id, f):
        filename = self.get_image_filename(image_id)
        print('Uploading image %s with size %d bytes.' % (filename, f.getbuffer().nbytes))
        f.seek(0)
        self.s3.upload_fileobj(
            f,
            S3_BUCKET_NAME,
            filename,
            ExtraArgs={
                'ACL': 'public-read',
                'ContentType': 'image/jpeg',
            }
        )
        return self.get_file_url(filename)
