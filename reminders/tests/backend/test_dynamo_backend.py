"""Tests for the DynamoDB backend functionality.

This module contains integration tests for the DynamoDB backend operations,
including creating, reading, updating, and deleting reminders. It tests both
single-user and shared reminder scenarios.
"""

from datetime import datetime

from chalicelib.backend.dynamodb import dynamo_backend
from dateutil.relativedelta import relativedelta


def test_create_single_reminder(reminders, reminders_model, new_reminder):
    """Test creating a single reminder."""
    reminder = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder)
    reminder_from_db = dynamo_backend.DynamoBackend.get_a_reminder_gsi(
        user_id="test_user_1", reminder_title="Test reminder"
    )
    for item in reminder_from_db:
        assert item.reminder_id == "abc"


def test_get_a_reminder_for_a_user(reminders, reminders_model, new_reminder):
    """Test the function get a reminder for a user."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    reminder_2 = new_reminder(
        reminder_id="abc", user_id="test_user_2", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    reminder_for_user_1 = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_1"
    )
    assert len(reminder_for_user_1) == 1
    reminder_for_user_2 = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_2"
    )
    assert len(reminder_for_user_2) == 1


def test_get_all_reminders_for_a_user(reminders, reminders_model, new_reminder):
    """Test the function get all reminders for a user."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    reminder_2 = new_reminder(
        reminder_id="def", user_id="test_user_1", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    all_reminders_for_user_1 = (
        dynamo_backend.DynamoBackend.get_all_reminders_for_a_user(user_id="test_user_1")
    )
    assert len(all_reminders_for_user_1) == 2
    reminder_ids = [reminder.reminder_id for reminder in all_reminders_for_user_1]
    assert sorted(reminder_ids) == sorted(["abc", "def"])


def test_update_a_reminder_for_a_user(reminders, reminders_model, new_reminder):
    """Test that updating a reminder for a single user works."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    reminder_1.reminder_description = "Changed reminder description"
    dynamo_backend.DynamoBackend.update_a_reminder(
        reminder_id="abc", updated_reminder=reminder_1.dict()
    )
    reminder_from_db = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_1"
    )
    for reminder in reminder_from_db:
        assert reminder.reminder_description == "Changed reminder description"


def test_update_a_reminder_works_for_a_shared_reminder(
    reminders, reminders_model, new_reminder
):
    """Test that updating a shared reminder works."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    reminder_2 = new_reminder(
        reminder_id="abc", user_id="test_user_2", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    reminder_1.reminder_description = "Changed reminder description"
    dynamo_backend.DynamoBackend.update_a_reminder(
        reminder_id="abc", updated_reminder=reminder_1.dict()
    )
    reminder_from_db_user_1 = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_1"
    )
    for reminder in reminder_from_db_user_1:
        assert reminder.reminder_description == "Changed reminder description"

    reminder_from_db_user_2 = dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
        reminder_id="abc", user_name="test_user_2"
    )
    for reminder in reminder_from_db_user_2:
        assert reminder.reminder_description == "Changed reminder description"


def test_get_a_reminder_gsi(reminders, reminders_model, new_reminder):
    """Test the function get_a_reminder_gsi."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    reminder_from_db_gsi = dynamo_backend.DynamoBackend.get_a_reminder_gsi(
        user_id="test_user_1", reminder_title="Test reminder"
    )
    all_reminders_from_db_gsi = list(reminder_from_db_gsi)
    assert len(all_reminders_from_db_gsi) == 1
    for reminder in all_reminders_from_db_gsi:
        assert reminder.reminder_id == "abc"
        assert reminder.reminder_title == "Test reminder"
        assert isinstance(reminder.reminder_expiration_date_time, datetime)
        expected_reminder_expiration_date_time = datetime.now() + relativedelta(
            months=1
        )
        assert datetime.strftime(
            reminder.reminder_expiration_date_time, "%d/%m/%y"
        ) == datetime.strftime(expected_reminder_expiration_date_time, "%d/%m/%y")


def test_delete_a_reminder(reminders, reminders_model, new_reminder):
    """Test delete a reminder."""
    reminder_1 = new_reminder(
        reminder_id="abc", user_id="test_user_1", reminder_title="Test reminder"
    )
    reminder_2 = new_reminder(
        reminder_id="def", user_id="test_user_1", reminder_title="Test reminder 2"
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    all_reminders_for_user_1 = (
        dynamo_backend.DynamoBackend.get_all_reminders_for_a_user(user_id="test_user_1")
    )
    assert len(all_reminders_for_user_1) == 2
    dynamo_backend.DynamoBackend.delete_a_reminder("abc")
    all_reminders_for_user_1 = (
        dynamo_backend.DynamoBackend.get_all_reminders_for_a_user(user_id="test_user_1")
    )
    assert len(all_reminders_for_user_1) == 1
