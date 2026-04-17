import os
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
import io
from flask import current_app

def get_s3_client():
    """Initializes and returns the boto3 client for Cloudflare R2."""
    return boto3.client(
        's3',
        endpoint_url=os.environ.get('R2_ENDPOINT_URL'),
        aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY'),
        config=Config(signature_version='s3v4')
    )

def upload_file_to_r2(file_storage_or_bytes, object_key):
    """
    Uploads a file to R2.
    file_storage_or_bytes can be a FileStorage object (from Flask request.files)
    or a bytes object.
    """
    s3 = get_s3_client()
    bucket = os.environ.get('R2_BUCKET_NAME')
    
    try:
        if isinstance(file_storage_or_bytes, bytes):
            s3.put_object(Bucket=bucket, Key=object_key, Body=file_storage_or_bytes)
        else:
            # It's a FileStorage object from Flask
            file_storage_or_bytes.seek(0)
            s3.upload_fileobj(file_storage_or_bytes, bucket, object_key)
        return True
    except ClientError as e:
        print(f"Error uploading to R2: {e}")
        return False

def download_file_from_r2(object_key):
    """
    Downloads a file from R2 and returns it as a BytesIO object.
    Useful for processing files in memory without saving to disk.
    """
    s3 = get_s3_client()
    bucket = os.environ.get('R2_BUCKET_NAME')
    
    try:
        response = s3.get_object(Bucket=bucket, Key=object_key)
        file_stream = io.BytesIO(response['Body'].read())
        return file_stream
    except ClientError as e:
        print(f"Error downloading from R2: {e}")
        return None

def get_presigned_url(object_key, expiration=3600):
    """
    Generates a pre-signed URL to temporarily allow downloading an object.
    """
    s3 = get_s3_client()
    bucket = os.environ.get('R2_BUCKET_NAME')
    
    try:
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': object_key},
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None
