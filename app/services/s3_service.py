import boto3
from botocore.exceptions import ClientError
from typing import Optional

from app.core.config import settings


class S3Service:
    def __init__(self):
        kwargs = {'region_name': settings.S3_REGION}

        if settings.S3_ACCESS_KEY_ID and settings.S3_SECRET_ACCESS_KEY:
            kwargs['aws_access_key_id'] = settings.S3_ACCESS_KEY_ID
            kwargs['aws_secret_access_key'] = settings.S3_SECRET_ACCESS_KEY

        self.s3_client = boto3.client('s3', **kwargs)
        self.bucket_name = settings.S3_BUCKET_NAME

    def upload_file(self, file_path: str, s3_key: str, content_type: str) -> str:
        try:
            with open(file_path, 'rb') as file:
                self.s3_client.upload_fileobj(
                    file,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': 'max-age=31536000'
                    }
                )

            url = f"https://{self.bucket_name}.s3.{settings.S3_REGION}.amazonaws.com/{s3_key}"
            return url

        except ClientError as e:
            raise Exception(f"S3 upload failed: {str(e)}")
        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")

    def delete_file(self, s3_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            print(f"S3 delete failed: {str(e)}")
            return False

    def get_public_url(self, s3_key: str) -> str:
        return f"https://{self.bucket_name}.s3.{settings.S3_REGION}.amazonaws.com/{s3_key}"
