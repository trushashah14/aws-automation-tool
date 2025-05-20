import pytest
from moto import mock_aws
import boto3
from aws_automation import s3
import os
from botocore.exceptions import BotoCoreError, ClientError


@pytest.fixture
def s3_client():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        yield client


def create_test_bucket_and_upload_files(s3_client, bucket_name):
    region = s3_client.meta.region_name
    if region == "us-east-1":
        s3_client.create_bucket(Bucket=bucket_name)
    else:
        s3_client.create_bucket(
            Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": region}
        )

    dummy_files = ["file1.txt", "file2.txt"]
    for file in dummy_files:
        with open(file, "w") as f:
            f.write("dummy content")

    s3.upload_objects(s3_client, bucket_name, dummy_files)
    return dummy_files


def cleanup_files(files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)


def test_download_objects(s3_client, tmp_path):
    bucket_name = "download-bucket"
    dummy_files = create_test_bucket_and_upload_files(s3_client, bucket_name)

    # Download files to tmp_path
    result = s3.download_objects(s3_client, bucket_name, dummy_files, str(tmp_path))
    assert result is True

    for file in dummy_files:
        assert (tmp_path / file).exists()

    cleanup_files(dummy_files)


def test_delete_objects(s3_client):
    bucket_name = "delete-objects-bucket"
    dummy_files = create_test_bucket_and_upload_files(s3_client, bucket_name)

    result = s3.delete_objects(s3_client, bucket_name, dummy_files)
    assert result is True

    remaining = s3.list_objects(s3_client, bucket_name, return_list=True)
    assert remaining == []

    cleanup_files(dummy_files)


def test_list_buckets_with_region_filter(s3_client):
    region = s3_client.meta.region_name
    s3.create_bucket(s3_client, "bucket1", region)
    s3.create_bucket(s3_client, "bucket2", region)

    buckets = s3.list_buckets(s3_client, region, return_list=True)
    assert isinstance(buckets, list)
    assert len(buckets) >= 2
    assert any(b["Bucket Name"] == "bucket1" for b in buckets)


def test_create_bucket_failure(s3_client):
    result = s3.create_bucket(s3_client, "", "us-east-1")
    assert result is False


def test_delete_bucket(s3_client):
    bucket_name = "test-delete-bucket"
    region = s3_client.meta.region_name
    assert s3.create_bucket(s3_client, bucket_name, region)

    dummy_files = ["file1.txt"]
    with open(dummy_files[0], "w") as f:
        f.write("dummy content")

    s3.upload_objects(s3_client, bucket_name, dummy_files)
    result = s3.delete_bucket(s3_client, bucket_name)
    assert result is True

    remaining_buckets = s3.list_buckets(s3_client, region, return_list=True)
    assert all(b["Bucket Name"] != bucket_name for b in remaining_buckets)

    cleanup_files(dummy_files)


def test_create_bucket_boto_core_error(s3_client):
    def mock_create_bucket(*args, **kwargs):
        raise BotoCoreError()

    s3_client.create_bucket = mock_create_bucket
    result = s3.create_bucket(s3_client, "fail-bucket", "us-east-1")
    assert result is False


def test_upload_objects_client_error(s3_client, tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("dummy content")

    def mock_upload_file(*args, **kwargs):
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        raise ClientError(error_response, "PutObject")

    s3_client.upload_file = mock_upload_file
    result = s3.upload_objects(s3_client, "any-bucket", [str(file_path)])
    assert result is False


def test_download_objects_boto_core_error(s3_client):
    def mock_download_file(*args, **kwargs):
        raise BotoCoreError("Simulated network error")

    s3_client.download_file = mock_download_file
    result = s3.download_objects(s3_client, "bucket", ["file.txt"], "/tmp")
    assert result is False


def test_delete_objects_client_error(s3_client):
    def mock_delete_object(*args, **kwargs):
        error_response = {"Error": {"Code": "NoSuchKey", "Message": "Key not found"}}
        raise ClientError(error_response, "DeleteObject")

    s3_client.delete_object = mock_delete_object
    result = s3.delete_objects(s3_client, "bucket", ["file.txt"])
    assert result is False


def test_list_buckets_client_error(s3_client):
    def mock_list_buckets(*args, **kwargs):
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}
        raise ClientError(error_response, "ListBuckets")

    s3_client.list_buckets = mock_list_buckets
    result = s3.list_buckets(s3_client, "us-east-1", return_list=True)
    assert result == []
