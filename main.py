import boto3 #Official AWS SDK for Python
import yaml #Used to read values from config.yaml
import argparse
import os
from botocore.exceptions import BotoCoreError, ClientError  # Boto3 exceptions
from aws_automation.ec2 import start_instance, stop_instance, terminate_instance, list_running_instances
from aws_automation.s3 import create_bucket , upload_file , list_files , delete_file, download_file, delete_bucket , list_buckets
from aws_automation.utils import load_config, logger


log = logger()

# Step 1: Create EC2 instance
def create_instance(ec2, config):
    try:
        log.info("Launching EC2 instance...")
        instance = ec2.create_instances(            #API call to AWS to create one (or more) EC2 instances.
            ImageId=config['aws']['ami_id'],   #AMI ID for the OS/image you want
            InstanceType=config['aws']['instance_type'],  #Size of instance (e.g., t2.micro).
            KeyName=config['aws']['key_name'], #Key pair name to allow SSH access.
            SecurityGroups=[config['aws']['security_group_name']],  #Security rules (e.g., allow SSH).
            MinCount=1,  #Create exactly one instance.
            MaxCount=1,  #Create exactly one instance.

            # Add human-readable names to your instances. (Very useful in AWS console!)
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [{'Key': 'Name', 'Value': config['aws']['instance_name']}]
                }
            ]
        )[0]  # [0] because create_instances returns a list of instances even if you ask of 1.We grab the first [0]
        return instance
    except ClientError as e:
        log.error(f"❌ AWS Client Error: {e.response['Error']['Message']}")
        exit(1)
    except BotoCoreError as e:
        log.error(f"❌ Boto3 Core Error: {str(e)}")
        exit(1)

# Step 2: Main function
def main():
    config = load_config()

    parser = argparse.ArgumentParser(
        description="AWS Automation CLI Tool - Manage EC2 and S3 resources easily.",
        epilog="Example: python main.py s3 list-buckets --region us-east-1"
        )
    subparsers = parser.add_subparsers(dest='command', help='Sub-command help')

    # EC2 Sub-command: create
    subparsers.add_parser('create', help='Create a new EC2 instance')

    # EC2 Sub-command: start
    parser_start = subparsers.add_parser('start', help='Start an existing EC2 instance')
    parser_start.add_argument('--instance-id', required=True, help='ID of the instance to start')

    # EC2 Sub-command: stop
    parser_stop = subparsers.add_parser('stop', help='Stop an existing EC2 instance')
    parser_stop.add_argument('--instance-id', required=True, help='ID of the instance to stop')

    # EC2 Sub-command: terminate
    parser_terminate = subparsers.add_parser('terminate', help='Terminate an existing EC2 instance')
    parser_terminate.add_argument('--instance-id', required=True, help='ID of the instance to terminate')

    # EC2 Sub-command: list
    subparsers.add_parser('list', help='List all running EC2 instances')

    #S3 Sub-command : create
    subparsers.add_parser('s3-create', help='Create an S3 bucket')

    #S3 Sub-command : upload
    parser_upload = subparsers.add_parser('s3-file-upload', help='Upload a file to your S3 bucket')
    parser_upload.add_argument('--file-path', required=True, help='Path of file to upload')

    #S3 Sub-command : list files
    subparsers.add_parser('s3-file-list', help='List all files in your S3 bucket')

    # S3 Sub-command : list buckets
    subparsers.add_parser('s3-bucket-list', help='List all S3 buckets in the configured region')

    #S3 Sub-command : download
    parser_download = subparsers.add_parser('s3-file-download', help='Download file(s) from S3 bucket')
    parser_download.add_argument('--file-names', nargs='+', required=True, help='Name of the file in S3 to download')

    #S3 Sub-command : delete files
    parser_delete = subparsers.add_parser('s3-file-delete', help='Delete file(s) from S3 bucket')
    parser_delete.add_argument('--file-names', nargs='+',required=True, help='Name of the file in S3 to delete')
    
    #S3 Sub-command : delete bucket
    subparsers.add_parser('s3-delete', help='Delete the configured S3 bucket')

    args = parser.parse_args()

    if args.command == 'create':
        config = load_config()  #name of the dictionary 
    
        
        # Create EC2 resource
        ec2 = boto3.resource('ec2', region_name=config['aws']['region_name'])  #resource is a higher-level API — easier to work with than client

        # Create instance
        instance = create_instance(ec2, config)

        # Wait for instance to be running
        log.info("Waiting for instance to run...")
        instance.wait_until_running()  #keeps polling AWS until your instance becomes running state.

        # Reload the instance attributes after running
        instance.load()  #updates the Python object with latest AWS data.

        log.info(f"Instance created successfully!")
        log.info(f"Instance ID: {instance.id}")
        log.info(f"Public IP Address: {instance.public_ip_address}")
        log.info(f"State: {instance.state['Name']}")

    elif args.command == 'start':
        start_instance(args.instance_id)

    elif args.command == 'stop':
        stop_instance(args.instance_id)

    elif args.command == 'terminate':
        terminate_instance(args.instance_id)
       
    elif args.command == 'list':
        list_running_instances()
        
    
    elif args.command == 's3-bucket-list':
        list_buckets(config)

    elif args.command == 's3-create':
        create_bucket(config)

    elif args.command == 's3-file-upload':
        upload_file(args.file_path, config)

    elif args.command == 's3-file-list':
        list_files(config)

    elif args.command == 's3-file-download':
        
        download_file(args.file_names, config)

    elif args.command == 's3-file-delete':
        confirm = input(f"⚠️ Are you sure you want to delete file(s)  {', '.join(args.file_names)}? [y/N]: ")
        if confirm.lower() == 'y':
        
            delete_file(args.file_names, config)
        else:
            log.info("❎ Deletion aborted by user.")

    elif args.command == 's3-delete':
        confirm = input(f"⚠️ Are you sure you want to delete bucket '{args.name}'? [y/N]: ")
        if confirm.lower() == 'y':
            delete_bucket(config)
        else:
            log.info("❎ Deletion aborted by user.")
    else:
        parser.print_help()

#Tells Python to run main() only if this file is executed directly (not imported somewhere else).

if __name__ == "__main__":
    main()
