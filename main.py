import boto3
import argparse
from botocore.exceptions import BotoCoreError, ClientError
from aws_automation.ec2 import (
    start_instance,
    stop_instance,
    terminate_instance,
    list_running_instances
)
from aws_automation.s3 import (
    create_bucket,
    upload_objects,
    list_objects,
    delete_objects,
    download_objects,
    delete_bucket,
    list_buckets,
    prompt_select_objects,
    prompt_select_buckets,
)
from aws_automation.utils import load_config, logger

log = logger()

def create_instance(ec2_resource, config):
    try:
        log.info("Launching EC2 instance...")
        instance = ec2_resource.create_instances(
            ImageId=config['aws']['ami_id'],
            InstanceType=config['aws']['instance_type'],
            KeyName=config['aws']['key_name'],
            SecurityGroups=[config['aws']['security_group_name']],
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': config['aws']['instance_name']}]
            }]
        )[0]

        log.info("Waiting for instance to run...")
        instance.wait_until_running()
        instance.load()

        log.info("✅ Instance created successfully!")
        log.info(f"Instance ID: {instance.id}")
        log.info(f"Public IP Address: {instance.public_ip_address}")
        log.info(f"State: {instance.state['Name']}")

        return instance

    except ClientError as e:
        log.error(f"❌ AWS Client Error: {e.response['Error']['Message']}")
        exit(1)
    except BotoCoreError as e:
        log.error(f"❌ Boto3 Core Error: {str(e)}")
        exit(1)

def main():
    config = load_config()

    s3_client = boto3.client('s3', region_name=config['s3']['region_name'])
    ec2_client = boto3.client('ec2', region_name=config['aws']['region_name'])
    ec2_resource = boto3.resource('ec2', region_name=config['aws']['region_name'])

    parser = argparse.ArgumentParser(
        description="AWS Automation CLI Tool - Manage EC2 and S3 resources easily.",
        epilog="Example: python main.py s3 list-buckets --region us-east-1"
    )
    subparsers = parser.add_subparsers(dest='command', help='Sub-command help')

    # EC2 commands
    subparsers.add_parser('create', help='Create a new EC2 instance')

    parser_start = subparsers.add_parser('start', help='Start an EC2 instance')
    parser_start.add_argument('--instance-id', required=True)

    parser_stop = subparsers.add_parser('stop', help='Stop an EC2 instance')
    parser_stop.add_argument('--instance-id', required=True)

    parser_terminate = subparsers.add_parser('terminate', help='Terminate an EC2 instance')
    parser_terminate.add_argument('--instance-id', required=True)

    subparsers.add_parser('list', help='List all running EC2 instances')

    # S3 commands
    subparsers.add_parser('s3-create', help='Create an S3 bucket')

    parser_upload = subparsers.add_parser('s3-obj-upload', help='Upload one or more objects to S3')
    parser_upload.add_argument('--obj-paths', nargs='+', required=True, help='Path(s) to the object(s) to upload')

    subparsers.add_parser('s3-obj-list', help='List objects in S3 bucket')

    subparsers.add_parser('s3-bucket-list', help='List S3 buckets')

    parser_download = subparsers.add_parser('s3-obj-download', help='Download object(s) from S3')
    parser_download.add_argument('--obj-names', nargs='+', help='Object name(s) to download')
    parser_download.add_argument(
        "--dest",
        default=".",
        help="Destination directory to download the object(s). Defaults to current directory."
    )
    parser_download.add_argument(
        '--interactive',
        action='store_true',
        help='Interactively select objects to download'
    )

    parser_delete = subparsers.add_parser('s3-obj-delete', help='Delete object(s) from S3')
    parser_delete.add_argument('--obj-names', nargs='+', help='Object name(s) to delete')
    parser_delete.add_argument(
        '--interactive',
        action='store_true',
        help='Interactively select objects to delete'
    )

    parser_bucket_delete = subparsers.add_parser('s3-delete', help='Delete one or more S3 buckets')
    parser_bucket_delete.add_argument(
        '--interactive',
        action='store_true',
        help='Interactively select buckets to delete'
    )
    parser_bucket_delete.add_argument(
        '--bucket-names',
        nargs='+',
        help='Name(s) of buckets to delete (ignored if --interactive is used)'
    )

    args = parser.parse_args()

    # EC2 actions
    if args.command == 'create':
        create_instance(ec2_resource, config)

    elif args.command == 'start':
        start_instance(ec2_client, args.instance_id)

    elif args.command == 'stop':
        stop_instance(ec2_client, args.instance_id)

    elif args.command == 'terminate':
        terminate_instance(ec2_client, args.instance_id)

    elif args.command == 'list':
        list_running_instances(ec2_client)

    # S3 actions
    elif args.command == 's3-create':
        create_bucket(s3_client, config['s3']['bucket_name'], config['s3']['region_name'])

    elif args.command == 's3-obj-upload':
        upload_objects(s3_client, config['s3']['bucket_name'], args.obj_paths)

    elif args.command == 's3-obj-list':
        list_objects(s3_client, config['s3']['bucket_name'])

    elif args.command == 's3-bucket-list':
        list_buckets(s3_client, config['s3']['region_name'])

    elif args.command == 's3-obj-download':
        obj_names = args.obj_names or []
        if args.interactive:
            obj_names = prompt_select_objects(s3_client, config['s3']['bucket_name'])
            if not obj_names:
                log.info("❎ No objects selected for download.")
                return
        if not obj_names:
            log.error("❌ No object names provided for download.")
            return
        download_objects(s3_client, config['s3']['bucket_name'], obj_names, args.dest)

    elif args.command == 's3-obj-delete':
        obj_names = args.obj_names or []
        if args.interactive:
            obj_names = prompt_select_objects(s3_client, config['s3']['bucket_name'])
            if not obj_names:
                log.info("❎ No objects selected for deletion.")
                return
        if not obj_names:
            log.error("❌ No object names provided for deletion.")
            return
        confirm = input(f"⚠️ Are you sure you want to delete object(s) {', '.join(obj_names)}? [y/N]: ")
        if confirm.lower() == 'y':
            delete_objects(s3_client, config['s3']['bucket_name'], obj_names)
        else:
            log.info("❎ Deletion aborted by user.")

    elif args.command == 's3-delete':
        bucket_names = args.bucket_names or []
        if args.interactive:
            bucket_names = prompt_select_buckets(s3_client, config['s3']['region_name'])
            if not bucket_names:
                log.info("❎ No buckets selected for deletion.")
                return
        if not bucket_names:
            # fallback to config bucket name if no bucket names provided
            bucket_names = [config['s3']['bucket_name']]

        for bucket_name in bucket_names:
            confirm = input(f"⚠️ Are you sure you want to delete bucket '{bucket_name}'? [y/N]: ")
            if confirm.lower() == 'y':
                delete_bucket(s3_client, bucket_name)
            else:
                log.info(f"❎ Deletion of bucket '{bucket_name}' aborted by user.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
