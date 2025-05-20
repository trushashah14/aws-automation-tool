import os
from botocore.exceptions import ClientError, BotoCoreError
from tabulate import tabulate
from aws_automation.utils import logger
import questionary

log = logger()


def bucket_exists(s3_client, bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError:
        return False


def object_exists(s3_client, bucket_name, obj_key):
    try:
        s3_client.head_object(Bucket=bucket_name, Key=obj_key)
        return True
    except ClientError:
        return False


def list_buckets(s3_client, region_name, return_list=False):
    try:
        response = s3_client.list_buckets()
        buckets = response.get('Buckets', [])
        if not buckets:
            log.info("No buckets found.")
            return [] if return_list else None

        if return_list:
            return [{"Bucket Name": b["Name"], "Creation Date": b["CreationDate"]} for b in buckets]
        else:
            log.info("Listing Buckets:\n" +
             tabulate(
                [[b["Name"], b["CreationDate"]] for b in buckets],
                headers=["Bucket Name", "Creation Date"],
                tablefmt="fancy_grid"
            ))
           
    except ClientError as e:
        log.error(f"Failed to list buckets: {e.response['Error']['Message']}")
        return [] if return_list else None
    
def prompt_select_buckets(s3_client, region_name):
    try:
        response = s3_client.list_buckets()
        all_buckets = response.get('Buckets', [])
        if region_name:
            buckets = [
                b['Name'] for b in all_buckets
                if s3_client.get_bucket_location(Bucket=b['Name'])['LocationConstraint'] == region_name
                or (region_name == 'us-east-1' and s3_client.get_bucket_location(Bucket=b['Name'])['LocationConstraint'] is None)
            ]
        else:
            buckets = [b['Name'] for b in all_buckets]

        if not buckets:
            log.warning("⚠️ No buckets available to select.")
            return []

        selected = questionary.checkbox(
            "Select bucket(s):",
            choices=buckets
        ).ask()

        return selected or []
    except ClientError as e:
        log.error(f"❌ Failed to fetch bucket list: {e.response['Error']['Message']}")
        return []

def prompt_select_objects(s3_client, bucket_name):
    try:
        object_list = list_objects(s3_client, bucket_name, return_list=True)
        if not object_list:
            log.warning(f"⚠️ No objects in bucket '{bucket_name}'.")
            return []

        selected = questionary.checkbox(
            f"Select object(s) from '{bucket_name}':",
            choices=object_list
        ).ask()

        return selected or []
    except ClientError as e:
        log.error(f"❌ Failed to fetch object list: {e.response['Error']['Message']}")
        return []

def create_bucket(s3_client, bucket_name, region_name):
    try:
        log.info(f"📦 Creating bucket {bucket_name}...")
        if region_name == "us-east-1":
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region_name},
            )
        log.info(f"✅ Bucket {bucket_name} created successfully!")
        return True
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Error while creating bucket: {str(e)}")
        return False


def upload_objects(s3_client, bucket_name, obj_paths):
    if not bucket_exists(s3_client, bucket_name):
        log.error(f"❌ Bucket {bucket_name} does not exist.")
        return False

    uploaded = 0
    try:
        for obj_path in obj_paths:
            if not os.path.exists(obj_path):
                log.warning(f"⚠️ File {obj_path} not found. Skipping.")
                continue
            obj_name = os.path.basename(obj_path)
            log.info(f"⬆️ Uploading {obj_name} to bucket {bucket_name}...")
            s3_client.upload_file(obj_path, bucket_name, obj_name)
            uploaded += 1
            log.info(f"✅ Uploaded {obj_name}")

        if uploaded == 0:
            log.info("⚠️ No files uploaded.")
        else:
            log.info("✅ Upload(s) completed.")
        return True
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Upload error: {str(e)}")
        return False



def list_objects(s3_client, bucket_name, return_list=False):
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        contents = response.get('Contents', [])
        if not contents:
            log.info(f"Bucket '{bucket_name}' is empty.")
            return [] if return_list else None

        if return_list:
            return [obj['Key'] for obj in contents]
        else:
            log.info(f"Listing Objects in bucket '{bucket_name}':\n"+
            tabulate(
                [[obj['Key'], obj['Size']] for obj in contents],
                headers=["Object Key", "Size (bytes)"],
                tablefmt="fancy_grid"
            ))
           
    except ClientError as e:
        log.error(f"Failed to list objects: {e.response['Error']['Message']}")
        return [] if return_list else None



def download_objects(s3_client, bucket_name, obj_names, dest_dir):
    if not bucket_exists(s3_client, bucket_name):
        log.error(f"❌ Bucket {bucket_name} does not exist.")
        return False

    downloaded = 0
    try:
        for obj_name in obj_names:
            if not object_exists(s3_client, bucket_name, obj_name):
                log.warning(f"⚠️ Object {obj_name} does not exist. Skipping.")
                continue
            dest_path = os.path.join(dest_dir, obj_name)
            log.info(f"⬇️  Downloading {obj_name} to {dest_path}")
            s3_client.download_file(bucket_name, obj_name, dest_path)
            downloaded += 1

        if downloaded == 0:
            log.info("⚠️ No objects downloaded.")
        else:
            log.info("✅ Download(s) completed.")
        return True
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Download error: {str(e)}")
        return False


def delete_objects(s3_client, bucket_name, obj_keys):
    if not bucket_exists(s3_client, bucket_name):
        log.error(f"❌ Bucket {bucket_name} does not exist.")
        return False

    deleted = 0
    try:
        for obj_key in obj_keys:
            if not object_exists(s3_client, bucket_name, obj_key):
                log.warning(f"⚠️ Object {obj_key} does not exist. Skipping.")
                continue
            log.info(f"🗑️ Deleting object {obj_key} from {bucket_name}")
            s3_client.delete_object(Bucket=bucket_name, Key=obj_key)
            deleted += 1

        if deleted == 0:
            log.info("⚠️ No objects deleted.")
        else:
            log.info("✅ Object(s) deleted successfully.")
        return True
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Deletion error: {str(e)}")
        return False


def delete_bucket(s3_client, bucket_name):
    if not bucket_exists(s3_client, bucket_name):
        log.error(f"❌ Bucket {bucket_name} does not exist.")
        return False

    try:
        log.info(f"🧹 Emptying bucket: {bucket_name}...")
        contents = list_objects(s3_client, bucket_name)
        for obj in contents:
            s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])

        log.info(f"🗑️ Deleting bucket: {bucket_name}...")
        s3_client.delete_bucket(Bucket=bucket_name)
        log.info("✅ Bucket deleted successfully.")
        return True
    except (ClientError, BotoCoreError) as e:
        log.error(f"❌ Error deleting bucket: {str(e)}")
        return False
