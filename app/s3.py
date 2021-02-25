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
        self.files = self.get_files()

    def get_files(self):
        paginator = self.s3.get_paginator('list_objects')
        page_iterator = paginator.paginate(Bucket=S3_BUCKET_NAME)
        files = set()
        for page in page_iterator:
            files.update({obj['Key'] for obj in page['Contents']})
        return files

    def get_image_filename(self, image_id, person):
        unique_identifier = '-'.join([
            str(image_id),
            person.get('netid', ''),
            str(person.get('upi', '')),
        ])
        image_name = hashlib.md5(unique_identifier.encode()).hexdigest()
        return image_name + '.jpg'

    def get_file_url(self, filename):
        return S3_LOCATION + filename

    def get_image_url(self, image_id=None, person=None, image_filename=None):
        if image_filename is None:
            image_filename = self.get_image_filename(image_id, person)
        return self.get_file_url(image_filename)

    def upload_image(self, f, filename):
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
