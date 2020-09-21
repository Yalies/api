import boto3
import botocore
import os

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

    def get_image_ids():
        objs = self.s3.list_objects(Bucket=S3_BUCKET_NAME)
        image_ids = {int(obj['Key'].rstrip('.jpg')) for obj in objs['Contents']}
        return image_ids

    def upload_image(image_id, f):
        filename = f'{image_id}.jpg'
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
        return '{}{}'.format(S3_LOCATION, filename)
