from tabulate import tabulate
from botocore.exceptions import ClientError, BotoCoreError  # Handle AWS/boto3 errors
from aws_automation.utils import logger

log = logger()


# Start an EC2 instance
def start_instance(ec2_client, instance_id):
    # Start a stopped EC2 instance.
    try:
        log.info(f"Starting instance {instance_id}...")
        response = ec2_client.start_instances(InstanceIds=[instance_id])
        log.info("✅ Instance started.")
        return response
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidInstanceID.NotFound":
            log.error(f"❌ Instance ID '{instance_id}' not found.")
        else:
            log.error(
                f"ClientError while starting instance: {e.response['Error']['Message']}"
            )
    except BotoCoreError as e:
        log.error(f"BotoCoreError while starting instance: {str(e)}")


# Stop an EC2 instance
def stop_instance(ec2_client, instance_id):

    try:
        log.info(f"Stopping instance {instance_id}...")
        response = ec2_client.stop_instances(InstanceIds=[instance_id])
        log.info("✅ Instance stopped sucessfully.")
        return response
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidInstanceID.NotFound":
            log.error(f"❌ Instance ID '{instance_id}' not found.")
        else:
            log.error(
                f"ClientError while stopping instance: {e.response['Error']['Message']}"
            )
    except BotoCoreError as e:
        log.error(f"BotoCoreError while stopping instance: {str(e)}")


# Terminate an EC2 instance
def terminate_instance(ec2_client, instance_id):
    # Terminate an EC2 instance permanently.

    try:
        confirm = input(
            f"⚠️ Are you sure you want to permanently TERMINATE instance '{instance_id}'? (yes/no): "
        )
        if confirm.lower() != "yes":
            log.info("Termination cancelled by user.")
            return None

        log.info(f"Terminating instance {instance_id}...")
        response = ec2_client.terminate_instances(InstanceIds=[instance_id])
        log.info("✅ Termination succesfull.")
        return response
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidInstanceID.NotFound":
            log.error(f"❌ Instance ID '{instance_id}' not found.")
        else:
            log.error(
                f"ClientError while terminating instance: {e.response['Error']['Message']}"
            )
    except BotoCoreError as e:
        log.error(f"BotoCoreError while terminating instance: {str(e)}")


# List all running EC2 instances
def list_running_instances(ec2_client):

    try:
        instances = []  # List to store instance info
        response = ec2_client.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )

        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instances.append(
                    {
                        "Instance ID": instance["InstanceId"],
                        "Type": instance["InstanceType"],
                        "Public IP": instance.get("PublicIpAddress", "N/A"),
                        "Private IP": instance.get("PrivateIpAddress", "N/A"),
                        "State": instance["State"]["Name"],
                    }
                )

        if instances:
            table = tabulate(instances, headers="keys", tablefmt="fancy_grid")
            log.info(f"Running EC2 instances:\n{table}")
        else:
            log.info("No running instances found.")
        return instances

    except ClientError as e:
        log.error(
            f"ClientError while listing instances: {e.response['Error']['Message']}"
        )
        return []
    except BotoCoreError as e:
        log.error(f"BotoCoreError while listing instances: {str(e)}")
        return []


# Example usage if you run ec2.py directly (Optional test block)
# if __name__ == "__main__":
#     log.("Listing running EC2 instances:")
#     running_instances = list_running_instances()
#     for idx, inst in enumerate(running_instances, start=1):
#         log.(f"{idx}. ID: {inst['InstanceId']}, Public IP: {inst.get('PublicIpAddress')}, State: {inst['State']}")
