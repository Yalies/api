import boto3
import botocore
import os

S3_BUCKET_NAME = 'yalestudentphotos'
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.environ.get('S3_SECRET_ACCESS_KEY')
S3_LOCATION = 'https://' + S3_BUCKET_NAME + '.s3.amazonaws.com/'

s3 = boto3.client(
   's3',
   aws_access_key_id=S3_ACCESS_KEY,
   aws_secret_access_key=S3_SECRET_ACCESS_KEY,
)

def upload_image(image_id, file):
    s3.upload_fileobj(
        file,
        S3_BUCKET_NAME,
        f'{image_id}.jpg',
        ExtraArgs={
            'ACL': 'public-read',
            'ContentType': file.content_type
        }
    )
    return '{}{}'.format(app.config['S3_LOCATION'], file.filename)
