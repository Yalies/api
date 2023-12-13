import botocore
import boto3
import os
import hashlib
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


S3_BUCKET_NAME = 'yalestudentphotos'
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.environ.get('S3_SECRET_ACCESS_KEY')
S3_LOCATION = 'https://' + S3_BUCKET_NAME + '.s3.amazonaws.com/'


# Define a dummy ImageUploader that doesn't perform any actions related to S3


class DummyImageUploader:
    def delete_unused_images(self, people):
        pass

    def get_image_filename(self, image_id, person):
        return ""

    def get_file_url(self, filename):
        return ""

    def upload_image(self, image, filename):
        # Return a placeholder image data (1x1 transparent PNG)
        placeholder_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00\x00\x00\x00\x90\x77\x53\xde\x00\x00\x00\x0cIDAT\x08\xd7c`\x00\x00\x00\x02\x00\x01\x8d\x8f\x0f\x00\x00\x00\x00IEND\xaeB`\x82'
        return placeholder_image_data


class ImageUploader:

    CHUNK_SIZE = 1000

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
            if page.get('Contents'):
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

    def upload_image(self, f, filename):
        logger.info('Uploading image %s with size %d bytes.' %
                    (filename, f.getbuffer().nbytes))
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

    def delete_unused_images(self, people):
        """
        :param people: list of people records of everyone scraped from face_book
        """
        filename_offset = len(S3_LOCATION)
        scraped_image_filenames = {
            person['img'][filename_offset:] for person in people if 'img' in person}
        to_delete = set(self.files) - scraped_image_filenames
        to_delete_objects = [{'Key': key} for key in to_delete]

        # delete_objects(...) will delete at most 1000 objects at a time
        for i in range(0, len(to_delete), self.CHUNK_SIZE):
            self.s3.delete_objects(
                Bucket=S3_BUCKET_NAME,
                Delete={
                    'Objects': to_delete_objects[i:i + self.CHUNK_SIZE],
                    'Quiet': True
                })

        logger.info('Deleted %d unused images.' % num_deleted)
