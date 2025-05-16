import pytest
from moto import mock_aws
import boto3
from aws_automation import s3
import os
from botocore.exceptions import BotoCoreError, ClientError


@pytest.fixture
def s3_client():
    with mock_aws():
        client = boto3.client('s3', region_name='us-east-1')
        yield client

def create_test_bucket_and_upload_files(s3_client, bucket_name):
    region = s3_client.meta.region_name
    if region == "us-east-1":
        s3_client.create_bucket(Bucket=bucket_name)
    else:
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region}
        )

    dummy_files = ["file1.txt", "file2.txt"]
    for file in dummy_files:
        with open(file, "w") as f:
            f.write("dummy content")

    s3.upload_objects(s3_client, bucket_name, dummy_files)  # CORRECT: use s3_client
    return dummy_files


def cleanup_files(files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)

def test_download_objects(s3_client):
    bucket_name = "download-bucket"
    dummy_files = create_test_bucket_and_upload_files(s3_client, bucket_name)

    result = s3.download_objects(s3_client, bucket_name, dummy_files)
    assert result is True

    cleanup_files(dummy_files)

def test_delete_objects(s3_client):
    bucket_name = "delete-objects-bucket"
    dummy_files = create_test_bucket_and_upload_files(s3_client, bucket_name)

    result = s3.delete_objects(s3_client, bucket_name, dummy_files)
    assert result is True

    objs = s3.list_objects(s3_client, bucket_name)
    assert objs == []

    cleanup_files(dummy_files)

def test_list_buckets_with_region_filter(s3_client):
    region = s3_client.meta.region_name
    s3.create_bucket(s3_client, "bucket1", region)
    s3.create_bucket(s3_client, "bucket2", region)

    buckets = s3.list_buckets(s3_client, region)
    assert isinstance(buckets, list)
    assert len(buckets) >= 2

def test_create_bucket_failure(s3_client):
    result = s3.create_bucket(s3_client, "", "us-east-1")
    assert result is False

def test_delete_bucket(s3_client):
    bucket_name = "test-delete-bucket"
    # Create bucket first
    assert s3.create_bucket(s3_client, bucket_name, s3_client.meta.region_name)
    # Upload a file to have content in the bucket
    dummy_files = ["file1.txt"]
    with open(dummy_files[0], "w") as f:
        f.write("dummy content")
    s3.upload_objects(s3_client, bucket_name, dummy_files)
    
    # Delete bucket (which should empty first)
    result = s3.delete_bucket(s3_client, bucket_name)
    assert result is True
    
    # Verify bucket no longer exists
    buckets = s3.list_buckets(s3_client, s3_client.meta.region_name)
    bucket_names = [b['Bucket Name'] for b in buckets]
    assert bucket_name not in bucket_names
    
    # Cleanup local file
    for f in dummy_files:
        if os.path.exists(f):
            os.remove(f)

def test_create_bucket_boto_core_error(s3_client):
    def mock_create_bucket(*args, **kwargs):
        exc = BotoCoreError()
        exc.args = ("Simulated network error",)
        raise exc
    s3_client.create_bucket = mock_create_bucket

    result = s3.create_bucket(s3_client, "test-bucket", "us-east-1")
    assert result is False

def test_upload_objects_client_error(s3_client, tmp_path):
    # Create dummy file
    file_path = tmp_path / "file.txt"
    file_path.write_text("dummy content")

    def mock_upload_file(*args, **kwargs):
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        raise ClientError(error_response, 'PutObject')

    s3_client.upload_file = mock_upload_file

    result = s3.upload_objects(s3_client, "bucket", [str(file_path)])
    assert result is False

def test_download_objects_boto_core_error(s3_client):
    def mock_download_file(*args, **kwargs):
        exc = BotoCoreError()
        exc.args = ("Simulated network error",)
        raise exc
    s3_client.download_file = mock_download_file

    result = s3.download_objects(s3_client, "bucket", ["file.txt"])
    assert result is False

def test_delete_objects_client_error(s3_client):
    def mock_delete_object(*args, **kwargs):
        error_response = {'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}}
        raise ClientError(error_response, 'DeleteObject')
    s3_client.delete_object = mock_delete_object

    result = s3.delete_objects(s3_client, "bucket", ["file.txt"])
    assert result is False

def test_list_buckets_client_error(s3_client):
    def mock_list_buckets(*args, **kwargs):
        error_response = {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}}
        raise ClientError(error_response, 'ListBuckets')
    s3_client.list_buckets = mock_list_buckets

    result = s3.list_buckets(s3_client, "us-east-1")
    assert result is None
