"""Module for conftest."""

import logging
import os
import sys
from datetime import datetime
from typing import Optional

import boto3
import pytest
from dateutil.relativedelta import relativedelta
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

# Configure project path
project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
logging.info("Using project root: %s", project_root)
sys.path.insert(0, project_root)

# Local imports after path setup
from chalicelib.backend.dynamodb import models
from chalicelib.data_structures import SingleReminder


@pytest.fixture(scope="session")
def dynamodb_container():
    """Start a DynamoDB local container."""
    container = DockerContainer("amazon/dynamodb-local:latest")
    container.with_command("-jar DynamoDBLocal.jar -sharedDb -inMemory")
    container.with_exposed_ports(8000)

    with container as container:
        # Wait for DynamoDB to be ready
        wait_for_logs(
            container, "Initializing DynamoDB Local with the following configuration"
        )
        port = container.get_exposed_port(8000)
        endpoint_url = f"http://localhost:{port}"
        yield endpoint_url


@pytest.fixture(scope="session")
def session():
    """Create boto3 session object."""
    return boto3.session.Session(
        aws_access_key_id="anything",
        aws_secret_access_key="anything",
        region_name="eu-central-1",
    )


@pytest.fixture()
def reminders(dynamodb_container, session):
    """Create dynamodb table on local dynamodb.

    Args:
        dynamodb_container: The DynamoDB container fixture
        session: The boto3 session fixture

    Yields:
        None: The table is created and ready for use
    """
    dynamodb = session.resource("dynamodb", endpoint_url=dynamodb_container)
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
                "IndexName": "UserIdReminderTitleGsi2",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "reminder_title", "KeyType": "RANGE"},
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": [
                        "reminder_expiration_date_time",
                        "reminder_id",
                        "reminder_tags",
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
def reminders_model(dynamodb_container):
    """Update reminders meta information for local testing.

    Args:
        dynamodb_container: The DynamoDB container fixture
    """
    models.Reminders.Meta.host = dynamodb_container
    models.Reminders.Meta.aws_access_key_id = "something"
    models.Reminders.Meta.aws_secret_access_key = "anything"


@pytest.fixture()
def new_reminder():
    """Create a fixture for generating new reminders.

    Returns:
        function: A factory function for creating SingleReminder instances
    """

    def _new_reminder(
        reminder_id: str,
        reminder_title: str,
        user_id: str,
        reminder_tags: Optional[list[str]] = None,
    ):
        """Create a new reminder.

        Args:
            reminder_id: Unique identifier for the reminder
            reminder_title: Title of the reminder
            user_id: ID of the user who owns the reminder
            reminder_tags: Optional list of tags for the reminder

        Returns:
            SingleReminder: A new reminder instance
        """
        return SingleReminder(
            reminder_id=reminder_id,
            user_id=user_id,
            reminder_title=reminder_title,
            reminder_description="Test reminder",
            reminder_tags=reminder_tags if reminder_tags is not None else ["Test"],
            reminder_frequency="once",
            should_expire=True,
            reminder_expiration_date_time=datetime.now() + relativedelta(months=1),
            next_reminder_date_time=datetime.now() + relativedelta(days=20),
            reminder_creation_time=datetime.now(),
        )

    return _new_reminder
