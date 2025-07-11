import boto3
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
from botocore.client import Config

class PrivateMediaStorage(S3Boto3Storage):
    location = 'private'
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False

    def url(self, name, parameters=None, expire=300):
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name=settings.AWS_S3_REGION_NAME
        )
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': self.location + '/' + name},
            ExpiresIn=expire
        )








# class StaticStorage(S3Boto3Storage):
#     location = 'static'
#     default_acl = 'public-read'


# class PublicMediaStorage(S3Boto3Storage):
#     location = 'media'
#     default_acl = 'public-read'
#     file_overwrite = False




