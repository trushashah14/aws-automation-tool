import os
from botocore.exceptions import ClientError, BotoCoreError
from tabulate import tabulate
from aws_automation.utils import logger

log = logger()

# Refactored: Accept s3_client and config as parameters
def create_bucket(s3_client, bucket_name, region_name):
    try:
        log.info(f"📦 Creating bucket {bucket_name}...")
        if region_name == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region_name}
            )
        log.info(f"✅ Bucket {bucket_name} created successfully!")
        return True
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Error while creating bucket: {str(e)}")
        return False

def upload_objects(s3_client, bucket_name, obj_paths):
    try:
        for obj_path in obj_paths:
            obj_name = os.path.basename(obj_path)
            log.info(f"⬆️ Uploading {obj_name} to bucket {bucket_name}...")
            s3_client.upload_file(obj_path, bucket_name, obj_name)
            log.info(f"✅ Object {obj_name} uploaded successfully!")
        return True
    except FileNotFoundError as e:
        log.error(f"❌ Error: File not found - {str(e)}")
        return False
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Error while uploading object(s): {str(e)}")
        return False


def list_objects(s3_client, bucket_name):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            objs = []
            for obj in response['Contents']:
                objs.append({
                    'Name': obj['Key'],
                    'Size (Bytes)': obj['Size'],
                    'Last Modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                })
            table = tabulate(objs, headers='keys', tablefmt='fancy_grid')
            log.info(f"Listing objects in bucket {bucket_name}:\n{table}")
            return objs
        else:
            log.info("Bucket is empty.")
            return []
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Error while listing objects: {str(e)}")
        return None

def download_objects(s3_client, bucket_name, obj_names):
    try:
        for obj_name in obj_names:
            log.info(f"⬇️  Downloading {obj_name} from bucket {bucket_name}...")
            s3_client.download_file(bucket_name, obj_name, obj_name)
        log.info("✅ Download(s) successful!")
        return True
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Error while downloading objects: {str(e)}")
        return False

def delete_objects(s3_client, bucket_name, obj_keys):
    try:
        for obj_key in obj_keys:
            log.info(f"🗑️ Deleting object {obj_key} from bucket {bucket_name}...")
            s3_client.delete_object(Bucket=bucket_name, Key=obj_key)
        log.info("✅ Object(s) deleted successfully!")
        return True
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Error while deleting objects: {str(e)}")
        return False

def delete_bucket(s3_client, bucket_name):
    try:
        log.info(f"Emptying bucket: {bucket_name}...")
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])

        log.info(f"🗑️ Deleting bucket: {bucket_name}...")
        s3_client.delete_bucket(Bucket=bucket_name)
        log.info("✅ Bucket deleted successfully.")
        return True
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Error deleting bucket: {str(e)}")
        return False

def list_buckets(s3_client, target_region):
    try:
        buckets = []
        for bucket in s3_client.list_buckets()['Buckets']:
            bucket_name = bucket['Name']
            loc = s3_client.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
            if loc is None:
                loc = 'us-east-1'
            if loc == target_region:
                buckets.append({
                    'Bucket Name': bucket_name,
                    'Region': loc,
                    'Creation Date': bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S')
                })
        if buckets:
            table = tabulate(buckets, headers='keys', tablefmt='fancy_grid')
            log.info(f"📦 Buckets in region {target_region}:\n{table}")
            return buckets
        else:
            log.info("❌ No buckets in this region.")
            return []
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Error while listing buckets: {str(e)}")
        return None
