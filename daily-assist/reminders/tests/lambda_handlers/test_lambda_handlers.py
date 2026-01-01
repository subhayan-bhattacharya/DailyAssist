"""Tests for lambda handler functions."""

import datetime
import re
from unittest.mock import MagicMock

import pytest
from core.backend.dynamodb import dynamo_backend
from core.lambda_handlers import query_and_send_reminders
from dateutil.relativedelta import relativedelta


def validate_message_body(
    message_body, expected_description, expected_expiration_datetime
):
    """Validate the format and content of the reminder message body.

    Args:
        message_body: The actual message body string
        expected_description: Expected reminder description
        expected_expiration_datetime: Expected expiration datetime object
    """
    # Check that the description is in the message
    assert (
        expected_description in message_body
    ), f"Description '{expected_description}' not found in: {message_body}"

    # Check that "Reminder due date:" is present
    assert (
        "Reminder due date:" in message_body
    ), f"'Reminder due date:' not found in: {message_body}"

    # Format the expected date string to match the lambda function format
    expected_date_str = expected_expiration_datetime.strftime("%d %B, %Y %H:%M")
    assert (
        expected_date_str in message_body
    ), f"Expected date '{expected_date_str}' not found in: {message_body}"

    # Validate the overall format:
    # "description \n Reminder due date: DD Month, YYYY HH:MM"
    expected_pattern = (
        rf"{re.escape(expected_description)} \n Reminder due date: "
        rf"{re.escape(expected_date_str)}"
    )
    assert re.match(
        expected_pattern, message_body
    ), f"Message doesn't match expected pattern. Got: {message_body}"


@pytest.fixture()
def mock_sns_client(mocker):
    """Mock SNS client."""
    mock_sns_client = MagicMock()
    mock_sns_response = {
        "MessageId": "test-message-id-123",
        "ResponseMetadata": {"HTTPStatusCode": 200},
    }
    mock_sns_client.publish.return_value = mock_sns_response

    # Mock boto3.client for SNS
    def mock_client(service_name):
        if service_name == "sns":
            return mock_sns_client
        return MagicMock()

    mocker.patch("boto3.client", side_effect=mock_client)

    return mock_sns_client


@pytest.fixture()
def mock_cognito_client(mocker):
    """Mock Cognito Identity Provider client."""
    mock_cognito_client = MagicMock()
    mock_cognito_response = {
        "UserAttributes": [
            {"Name": "email", "Value": "test@example.com"},
            {"Name": "sub", "Value": "test-user-id-123"},
        ]
    }
    mock_cognito_client.admin_get_user.return_value = mock_cognito_response

    # Mock boto3.session.Session().client for Cognito
    def mock_session_client(service_name):
        if service_name == "cognito-idp":
            return mock_cognito_client
        return MagicMock()

    mocker.patch("boto3.session.Session.client", side_effect=mock_session_client)

    return mock_cognito_client


@pytest.fixture()
def reminder_due_today(new_reminder):
    """Create a reminder that is due today."""
    today = datetime.datetime.now()
    reminder = new_reminder(
        reminder_id="reminder-due-today",
        user_id="test_user_1",
        reminder_title="Today's Reminder",
        reminder_tags=["urgent"],
    )
    reminder.next_reminder_date_time = today
    return reminder


@pytest.fixture()
def reminder_due_tomorrow(new_reminder):
    """Create a reminder that is due tomorrow."""
    tomorrow = datetime.datetime.now() + relativedelta(days=1)
    reminder = new_reminder(
        reminder_id="reminder-due-tomorrow",
        user_id="test_user_1",
        reminder_title="Tomorrow's Reminder",
        reminder_tags=["future"],
    )
    reminder.next_reminder_date_time = tomorrow
    return reminder


@pytest.fixture()
def event_data():
    """Create test event data for the lambda function."""
    return {
        "users": [
            {
                "username": "test_user_1",
                "message_arn": "arn:aws:sns:us-east-1:123456789012:test-topic",
            }
        ],
        "user_pool_id": "us-east-1_TestPool123",
    }


def test_query_and_send_reminders_with_reminders_due_today(
    reminders_model,
    reminders,
    reminder_due_today,
    event_data,
    mock_sns_client,
    mock_cognito_client,
):
    """Test query_and_send_reminders when there are reminders due today."""
    # Create the reminder in the database
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_due_today)

    # Call the function
    result = query_and_send_reminders(event_data, None)

    # Verify the structure of the response
    assert "details" in result
    assert "test_user_1" in result["details"]

    user_details = result["details"]["test_user_1"]
    assert "email" in user_details
    assert "notifications" in user_details
    assert user_details["email"] == "test@example.com"

    # Should have one notification since one reminder is due today
    assert len(user_details["notifications"]) == 1

    notification = user_details["notifications"][0]
    assert "sns_response" in notification
    assert "message_body" in notification

    # Validate the message body content and format
    validate_message_body(
        notification["message_body"],
        reminder_due_today.reminder_description,
        reminder_due_today.reminder_expiration_date_time,
    )

    # Verify SNS was called
    mock_sns_client.publish.assert_called_once()
    call_args = mock_sns_client.publish.call_args
    assert call_args[1]["TopicArn"] == "arn:aws:sns:us-east-1:123456789012:test-topic"
    assert "Test reminder" in call_args[1]["Message"]

    # Verify Cognito was called
    mock_cognito_client.admin_get_user.assert_called_once_with(
        UserPoolId="us-east-1_TestPool123", Username="test_user_1"
    )


def test_query_and_send_reminders_with_no_reminders_due_today(
    reminders_model,
    reminders,
    reminder_due_tomorrow,
    event_data,
    mock_sns_client,
    mock_cognito_client,
):
    """Test query_and_send_reminders when no reminders are due today."""
    # Create a reminder due tomorrow (not today)
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_due_tomorrow)

    # Call the function
    result = query_and_send_reminders(event_data, None)

    # Verify the response structure
    assert "details" in result
    assert "test_user_1" in result["details"]

    user_details = result["details"]["test_user_1"]
    assert "email" in user_details
    assert "notifications" in user_details

    # Should have no notifications since no reminders are due today
    assert len(user_details["notifications"]) == 0

    # Verify SNS was not called
    mock_sns_client.publish.assert_not_called()

    # Verify Cognito was still called to get user email
    mock_cognito_client.admin_get_user.assert_called_once()


def test_query_and_send_reminders_with_multiple_reminders_due_today(
    reminders_model,
    reminders,
    new_reminder,
    event_data,
    mock_sns_client,
    mock_cognito_client,
):
    """Test query_and_send_reminders with multiple reminders due today."""
    today = datetime.datetime.now()

    # Create two reminders due today
    reminder_1 = new_reminder(
        reminder_id="reminder-1",
        user_id="test_user_1",
        reminder_title="First Reminder",
        reminder_tags=["tag1"],
    )
    reminder_1.next_reminder_date_time = today

    reminder_2 = new_reminder(
        reminder_id="reminder-2",
        user_id="test_user_1",
        reminder_title="Second Reminder",
        reminder_tags=["tag2"],
    )
    reminder_2.next_reminder_date_time = today

    # Create the reminders in the database
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)

    # Call the function
    result = query_and_send_reminders(event_data, None)

    # Verify two notifications were sent
    user_details = result["details"]["test_user_1"]
    assert len(user_details["notifications"]) == 2

    # Validate both message bodies
    notifications = user_details["notifications"]

    # We need to match notifications with their corresponding reminders
    # Since the order might not be guaranteed, we'll check both possibilities

    # Check that both reminder descriptions are present in the messages
    reminder_1_desc = reminder_1.reminder_description
    reminder_2_desc = reminder_2.reminder_description

    # Find which message corresponds to which reminder
    for notification in notifications:
        message_body = notification["message_body"]
        if reminder_1_desc in message_body:
            validate_message_body(
                message_body, reminder_1_desc, reminder_1.reminder_expiration_date_time
            )
        elif reminder_2_desc in message_body:
            validate_message_body(
                message_body, reminder_2_desc, reminder_2.reminder_expiration_date_time
            )
        else:
            pytest.fail(f"Message body doesn't match either reminder: {message_body}")

    # Verify SNS was called twice
    assert mock_sns_client.publish.call_count == 2


def test_query_and_send_reminders_missing_users_parameter():
    """Test query_and_send_reminders when users parameter is missing."""
    event_without_users = {"user_pool_id": "test-pool"}

    with pytest.raises(
        ValueError,
        match="The data for the lambda function needs to accept a list of users!",
    ):
        query_and_send_reminders(event_without_users, None)


def test_query_and_send_reminders_with_multiple_users(
    reminders_model, reminders, new_reminder, mock_sns_client, mock_cognito_client
):
    """Test query_and_send_reminders with multiple users."""
    today = datetime.datetime.now()

    # Create reminders for two different users
    reminder_user1 = new_reminder(
        reminder_id="reminder-user1",
        user_id="test_user_1",
        reminder_title="User 1 Reminder",
        reminder_tags=["user1"],
    )
    reminder_user1.next_reminder_date_time = today

    reminder_user2 = new_reminder(
        reminder_id="reminder-user2",
        user_id="test_user_2",
        reminder_title="User 2 Reminder",
        reminder_tags=["user2"],
    )
    reminder_user2.next_reminder_date_time = today

    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_user1)
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_user2)

    # Event data with multiple users
    event_data = {
        "users": [
            {
                "username": "test_user_1",
                "message_arn": "arn:aws:sns:us-east-1:123456789012:user1-topic",
            },
            {
                "username": "test_user_2",
                "message_arn": "arn:aws:sns:us-east-1:123456789012:user2-topic",
            },
        ],
        "user_pool_id": "us-east-1_TestPool123",
    }

    # Call the function
    result = query_and_send_reminders(event_data, None)

    # Verify both users are in the response
    assert "test_user_1" in result["details"]
    assert "test_user_2" in result["details"]

    # Each user should have one notification
    assert len(result["details"]["test_user_1"]["notifications"]) == 1
    assert len(result["details"]["test_user_2"]["notifications"]) == 1

    # Validate message bodies for both users
    user1_notification = result["details"]["test_user_1"]["notifications"][0]
    user2_notification = result["details"]["test_user_2"]["notifications"][0]

    validate_message_body(
        user1_notification["message_body"],
        reminder_user1.reminder_description,
        reminder_user1.reminder_expiration_date_time,
    )

    validate_message_body(
        user2_notification["message_body"],
        reminder_user2.reminder_description,
        reminder_user2.reminder_expiration_date_time,
    )

    # Verify SNS was called twice (once for each user)
    assert mock_sns_client.publish.call_count == 2

    # Verify Cognito was called twice (once for each user)
    assert mock_cognito_client.admin_get_user.call_count == 2
