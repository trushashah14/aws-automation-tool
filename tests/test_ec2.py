import boto3
import pytest
from moto import mock_aws
from aws_automation.ec2 import start_instance, stop_instance, terminate_instance, list_running_instances
from botocore.exceptions import ClientError
from botocore.exceptions import BotoCoreError

# Use a fixed region for all tests
REGION = "us-east-1"

@pytest.fixture
def ec2_client():
    with mock_aws():
        client = boto3.client("ec2", region_name=REGION)
        yield client

@pytest.fixture
def instance_id(ec2_client):
    # Launch a test instance
    reservation = ec2_client.run_instances(
        ImageId="ami-12345678",  # Dummy AMI for moto
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=1
    )
    return reservation['Instances'][0]['InstanceId']

def test_start_instance(ec2_client, instance_id):
    # Stop the instance first to allow starting
    ec2_client.stop_instances(InstanceIds=[instance_id])
    response = start_instance(ec2_client, instance_id)
    assert response["StartingInstances"][0]["InstanceId"] == instance_id

def test_stop_instance(ec2_client, instance_id):
    response = stop_instance(ec2_client, instance_id)
    assert response["StoppingInstances"][0]["InstanceId"] == instance_id

def test_terminate_instance(monkeypatch, ec2_client, instance_id):
    # Auto-confirm termination by monkeypatching input
    monkeypatch.setattr("builtins.input", lambda _: "yes")
    response = terminate_instance(ec2_client, instance_id)
    assert response["TerminatingInstances"][0]["InstanceId"] == instance_id

def test_list_running_instances(ec2_client, instance_id):
    instances = list_running_instances(ec2_client)
    assert any(inst["Instance ID"] == instance_id for inst in instances)

def test_terminate_instance_cancel(monkeypatch, ec2_client, instance_id):
    monkeypatch.setattr("builtins.input", lambda _: "no")
    response = terminate_instance(ec2_client, instance_id)
    assert response is None




def test_start_instance_invalid_id(ec2_client):
    invalid_id = "i-invalid1234"

    # Patch client to raise ClientError for invalid instance id
    def mock_start_instances(*args, **kwargs):
        raise ClientError(
            {"Error": {"Code": "InvalidInstanceID.NotFound", "Message": "Invalid instance ID"}},
            "StartInstances"
        )

    ec2_client.start_instances = mock_start_instances

    result = start_instance(ec2_client, invalid_id)
    assert result is None



def test_stop_instance_boto_core_error(ec2_client):
    def mock_stop_instances(*args, **kwargs):
        exc = BotoCoreError()
        exc.args = ("Network error",)  # optional, to add a message
        raise exc

    ec2_client.stop_instances = mock_stop_instances

    result = stop_instance(ec2_client, "i-1234567890abcdef0")
    assert result is None


def test_list_running_instances_client_error(ec2_client):
    def mock_describe_instances(*args, **kwargs):
        raise ClientError(
            {"Error": {"Code": "UnauthorizedOperation", "Message": "Not authorized"}},
            "DescribeInstances"
        )

    ec2_client.describe_instances = mock_describe_instances

    instances = list_running_instances(ec2_client)
    assert instances == []


def test_terminate_instance_invalid_id(monkeypatch, ec2_client):
    monkeypatch.setattr("builtins.input", lambda _: "yes")

    def mock_terminate_instances(*args, **kwargs):
        raise ClientError(
            {"Error": {"Code": "InvalidInstanceID.NotFound", "Message": "Instance not found"}},
            "TerminateInstances"
        )

    ec2_client.terminate_instances = mock_terminate_instances

    response = terminate_instance(ec2_client, "i-invalidid")
    assert response is None
