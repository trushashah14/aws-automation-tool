import boto3
import yaml
import os
from botocore.exceptions import ClientError, BotoCoreError
from aws_automation.utils import load_config, logger
from tabulate import tabulate

log= logger()

# Get S3 client
def get_s3_client():
    config = load_config()
    return boto3.client('s3', region_name=config['s3']['region_name'])

# Create a new S3 bucket
def create_bucket(config):
    s3_client = get_s3_client()
    bucket_name = config['s3']['bucket_name']

    try:
        log.info(f"📦 Creating bucket {bucket_name}...")
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': config['s3']['region_name']}
        )
        log.info(f"✅ Bucket {bucket_name} created successfully!")
    except ClientError as e:
        log.error(f"❌ ClientError while creating bucket: {e.response['Error']['Message']}")
    except BotoCoreError as e:
        log.error(f"❌ BotoCoreError while creating bucket: {str(e)}")

# Upload a file to S3
def upload_file(file_path,config):
    s3_client = get_s3_client()
    bucket_name = config['s3']['bucket_name']
    try:
        file_name = os.path.basename(file_path)
        log.info(f"⬆️ Uploading {file_name} to bucket {bucket_name}...")
        s3_client.upload_file(file_path, bucket_name, file_name)
        log.info(f"✅ File {file_name} uploaded successfully!")
    except FileNotFoundError:
        log.error("❌ Error: File not found.")
    except ClientError as e:
        log.error(f"❌ ClientError while uploading file: {e.response['Error']['Message']}")
    except BotoCoreError as e:
        log.error(f"❌ BotoCoreError while uploading file: {str(e)}")

# List all files in S3 bucket
def list_files(config):
    s3_client = get_s3_client()
    bucket_name = config['s3']['bucket_name']

    try:
    
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            files = []
            for obj in response['Contents']:
                files.append({
                    'File Name': obj['Key'],
                    'Size (Bytes)': obj['Size'],
                    'Last Modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                })

            table = tabulate(files, headers='keys', tablefmt='fancy_grid')
            log.info(f"Listing files in bucket {bucket_name}: \n{table}")  # Log each line of the table separately
        else:
            log.info("Bucket is empty.")
    except ClientError as e:
        log.error(f"❌ ClientError while listing files: {e.response['Error']['Message']}")
    except BotoCoreError as e:
        log.error(f"❌ BotoCoreError while listing files: {str(e)}")

# Download  file from S3 bucket
def download_file(file_names, config):
    s3_client = get_s3_client()
    bucket_name = config['s3']['bucket_name']

    try:
        for file_name in file_names:
            log.info(f"⬇️  Downloading {file_name} from S3 bucket {bucket_name}...")
            s3_client.download_file(bucket_name, file_name, file_name)
            log.info("✅ Download successful!")
    except ClientError as e:
        log.error(f"❌ AWS Client Error: {e.response['Error']['Message']}")
    except BotoCoreError as e:
        log.error(f"❌ Boto3 Core Error: {str(e)}")

# Delete a file from S3 bucket
def delete_file(file_keys,config):
    s3_client = get_s3_client()
    bucket_name = config['s3']['bucket_name']

    try:
        for file_key in file_keys:
            log.info(f"🗑️ Deleting file {file_key} from bucket {bucket_name}...")
            s3_client.delete_object(Bucket=bucket_name, Key=file_key)
            log.info(f"✅ File {file_key} deleted successfully!")
    except ClientError as e:
        log.error(f"❌ ClientError while deleting file: {e.response['Error']['Message']}")
    except BotoCoreError as e:
        log.error(f"❌ BotoCoreError while deleting file: {str(e)}")


# Delete a bucket
def delete_bucket(config):
    bucket_name = config['s3']['bucket_name']
    s3 = get_s3_client()

    # Empty the bucket first
    try:
        log.info(f"Emptying bucket: {bucket_name}...")
        response = s3.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3.delete_object(Bucket=bucket_name, Key=obj['Key'])

        # Now delete the bucket
        log.info(f"🗑️ Deleting bucket: {bucket_name}...")
        s3.delete_bucket(Bucket=bucket_name)
        log.info("✅ Bucket deleted successfully.")
    except ClientError as e:
        log.error(f"❌ Error deleting bucket: {e.response['Error']['Message']}")

#list buckets in provided region
def list_buckets(config):
    s3_client = get_s3_client()
    target_region = config['s3']['region_name']

    try:
       
        buckets =[]
        for bucket in s3_client.list_buckets()['Buckets']:
            bucket_name = bucket['Name']
            loc = s3_client.get_bucket_location(Bucket=bucket['Name'])['LocationConstraint']
            if loc == target_region:
                buckets.append({
                    'Bucket Name': bucket_name,
                    'Region': loc,
                    'Creation Date': bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S')
                })
        if buckets:
            table = tabulate(buckets, headers='keys', tablefmt='fancy_grid')
            log.info(f"📦 Buckets in region {target_region}: \n{table}")
        else:
            log.info("❌ No buckets in this region.")
    except ClientError as e:
        log.error(f"❌ ClientError while listing buckets: {e.response['Error']['Message']}")
    except BotoCoreError as e:
        log.error(f"❌ BotoCoreError while listing buckets: {str(e)}")

