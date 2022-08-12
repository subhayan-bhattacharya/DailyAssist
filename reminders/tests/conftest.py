"""Module for conftest."""

import os
import sys

import boto3
import pytest

project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

sys.path.insert(0, project_root)

from chalicelib.backend.dynamodb import models


@pytest.fixture(scope="session")
def docker_compose_files(pytestconfig):
    """Get the docker-compose.yml absolute path.
    Override this fixture in your tests if you need a custom location.
    """
    return [pytestconfig.invocation_dir / "tests/docker-compose.yml"]


@pytest.fixture(scope="session")
def docker_app(docker_services):
    """Start the dynamodb application."""
    docker_services.start("dynamodb-local")
    public_port = docker_services.wait_for_service("dynamodb-local", 8000)
    url = "http://{docker_services.docker_ip}:{public_port}".format(**locals())
    return url


@pytest.fixture(scope="session")
def session():
    """Create boto3 session object."""
    return boto3.session.Session(profile_name="dynamo_local")


@pytest.fixture()
def reminders(docker_app, session):
    """Create dynamodb table on local dynamodb."""
    dynamodb = session.resource("dynamodb", endpoint_url=docker_app)
    dynamodb.create_table(
        TableName="Reminders",
        KeySchema=[
            {"AttributeName": "reminder_id", "KeyType": "HASH"},
            {"AttributeName": "user_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "reminder_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "reminder_title", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "UserIdReminderTitleGsi",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "reminder_title", "KeyType": "RANGE"},
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": [
                        "reminder_expiration_date_time",
                        "reminder_id",
                    ],
                },
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    yield
    # Delete the above table so that we can start afresh
    table = dynamodb.Table("Reminders")
    table.delete()


@pytest.fixture()
def reminders_model(docker_app):
    """Update reminders meta information for local testing."""
    models.Reminders.Meta.host = docker_app
    models.Reminders.Meta.aws_access_key_id = "something"
    models.Reminders.Meta.aws_secret_access_key = "anything"
