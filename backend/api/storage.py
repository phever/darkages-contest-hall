import re

import boto3
from botocore.config import Config
from django.conf import settings


def s3_client():
    return boto3.client(
        's3',
        endpoint_url=settings.ARCHIVE_S3_ENDPOINT,
        aws_access_key_id=settings.ARCHIVE_S3_ACCESS_KEY,
        aws_secret_access_key=settings.ARCHIVE_S3_SECRET_KEY,
        region_name=settings.ARCHIVE_S3_REGION,
        # MinIO behind a reverse proxy → path-style addressing, SigV4.
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
    )


def safe_key(entry_id, filename):
    base = re.sub(r'[^A-Za-z0-9._-]', '_', filename or 'file')[:120].strip('._') or 'file'
    return f"entries/{entry_id}/{base}"


def presign_put(key, content_type, expires=600):
    return s3_client().generate_presigned_url(
        'put_object',
        Params={'Bucket': settings.ARCHIVE_S3_BUCKET, 'Key': key, 'ContentType': content_type},
        ExpiresIn=expires,
    )


def public_url(key):
    return f"{settings.ARCHIVE_PUBLIC_BASE_URL.rstrip('/')}/{settings.ARCHIVE_S3_BUCKET}/{key}"


def is_configured():
    return bool(settings.ARCHIVE_S3_ACCESS_KEY and settings.ARCHIVE_S3_SECRET_KEY)
