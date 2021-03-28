import boto3
import botocore
import os
from io import StringIO
import json


S3_BUCKET_NAME = 'yalies'
S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY')
S3_SECRET_ACCESS_KEY = os.environ.get('S3_SECRET_ACCESS_KEY')
S3_LOCATION = 'https://' + S3_BUCKET_NAME + '.s3.amazonaws.com/'


class Cache:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        )

    def get_file_url(self, filename):
        return S3_LOCATION + filename

    def get(self, key):
        filename = key + '.json'
        try:
            body = self.s3.get_object(
                Bucket=S3_BUCKET_NAME,
                Key=filename,
            )
        except:
            return None
        if body:
            body = body['Body'].read()
            return json.loads(body.decode())
        return None

    def set(self, key, data):
        filename = key + '.json'
        local_path = '/tmp/' + filename
        with open(local_path, 'w') as f:
            json.dump(data, f)
        print(f'Uploading cache {key}.')
        self.s3.upload_file(
            local_path,
            S3_BUCKET_NAME,
            filename,
        )
        return self.get_file_url(filename)

    def delete(self, key):
        filename = key + '.json'
        self.s3.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=filename,
        )
