"""Tests for the main Chalice application."""

import json
from datetime import datetime

import pytest
from app import app
from chalice.test import Client
from chalicelib import data_structures
from chalicelib.backend.dynamodb import dynamo_backend
from dateutil.relativedelta import relativedelta


@pytest.fixture()
def new_reminder_request():
    """Create a dummy new reminder request."""
    return {
        "reminder_title": "Dummy reminder",
        "reminder_description": "Description",
        "reminder_tags": ["doctor"],
        "reminder_frequency": "once",
        "should_expire": True,
        "reminder_expiration_date_time": (
            f"{datetime.strftime(datetime.now() + relativedelta(months=1), '%d/%m/%y')}"
            f" 10:00"
        ),
        "reminder_id": "6850f2e9-f920-11ec-a7c5-416944df2ab7",
    }


def test_create_a_new_reminder_normal_use_case(
    reminders_model, reminders, new_reminder_request, mocker
):
    """Test the function create a new reminder from app."""
    mocked_send_confirmation = mocker.patch("chalicelib.utils.send_user_confirmation")
    mocked_get_user_details = mocker.patch(
        "chalicelib.utils.get_user_details_from_context"
    )
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )
    reminder_from_db = dynamo_backend.DynamoBackend.get_a_reminder_gsi(
        user_id="Test user", reminder_title=new_reminder_request["reminder_title"]
    )
    assert len(list(reminder_from_db)) == 0

    with Client(app) as client:
        response = client.http.post("/reminders", body=json.dumps(new_reminder_request))
    returned_body = json.loads(response.body)
    assert returned_body["message"] == "New reminder successfully created!"
    assert "reminderId" in returned_body
    reminder_id_in_response = returned_body["reminderId"]

    # We check if the new reminder is really created
    # We just use our database methods to test the backend
    reminder_from_db = list(
        dynamo_backend.DynamoBackend.get_a_reminder_gsi(
            user_id="test_user_1", reminder_title=new_reminder_request["reminder_title"]
        )
    )
    assert len(reminder_from_db) == 1
    assert reminder_from_db[0].reminder_id == reminder_id_in_response

    # Verify that send_user_confirmation was called with the correct arguments
    mocked_send_confirmation.assert_called_once()
    call_args = mocked_send_confirmation.call_args
    assert call_args[0][0] == "test_user_1"  # username
    assert "01/09/25 10:00" in call_args[0][1]  # expiration date in message
    assert "Description" in call_args[0][1]  # reminder_description in message
    assert "New reminder added for date" in call_args[0][1]


def test_share_a_reminder(
    reminders_model, reminders, new_reminder_request, new_reminder, mocker
):
    """Share a reminder with another user."""
    mocked_send_confirmation = mocker.patch("chalicelib.utils.send_user_confirmation")
    mocked_get_user_details = mocker.patch(
        "chalicelib.utils.get_user_details_from_context"
    )
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )
    # First create a new reminder in db.
    reminder = new_reminder(
        reminder_id=new_reminder_request["reminder_id"],
        user_id="test_user_1",
        reminder_title=new_reminder_request["reminder_title"],
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder)
    reminder_from_db = list(
        dynamo_backend.DynamoBackend.get_a_reminder_gsi(
            user_id="test_user_1", reminder_title=new_reminder_request["reminder_title"]
        )
    )
    reminder_id = reminder_from_db[0].reminder_id
    with Client(app) as client:
        response = client.http.post(
            f"/reminders/{reminder_id}", body=json.dumps({"username": "test_user_2"})
        )
    returned_body = json.loads(response.body)
    assert response.status_code == 200
    assert returned_body == {"message": "Reminder successfully shared!"}

    # We check in the database to ensure that the reminder was shared successfully
    reminder_from_db_user_2 = list(
        dynamo_backend.DynamoBackend.get_a_reminder_gsi(
            user_id="test_user_2", reminder_title=new_reminder_request["reminder_title"]
        )
    )
    assert len(reminder_from_db_user_2) == 1
    assert reminder_from_db_user_2[0].reminder_id == new_reminder_request["reminder_id"]

    # compare the above reminder with the one that user 1 has
    reminder_from_db_user_1 = list(
        dynamo_backend.DynamoBackend.get_a_reminder_gsi(
            user_id="test_user_1", reminder_title=new_reminder_request["reminder_title"]
        )
    )
    assert len(reminder_from_db_user_1) == 1
    assert (
        reminder_from_db_user_2[0].reminder_id == reminder_from_db_user_1[0].reminder_id
    )

    # Verify that send_user_confirmation was called with the correct arguments
    mocked_send_confirmation.assert_called_once()
    call_args = mocked_send_confirmation.call_args
    assert call_args[0][0] == "test_user_1"  # original_user
    assert "test_user_2" in call_args[0][1]  # username_to_be_shared_with in message
    assert "Test reminder" in call_args[0][1]  # reminder_description in message
    assert "Reminder shared with user: test_user_2" in call_args[0][1]


def test_view_list_of_all_reminders_for_a_user(
    reminders_model, reminders, new_reminder, mocker
):
    """Test the function get_all_reminders_for_a_user."""
    mocked_get_user_details = mocker.patch("app.get_user_details_from_context")
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )
    # Create a couple of dummy reminders
    reminder_1 = new_reminder(
        reminder_id="abc",
        user_id="test_user_1",
        reminder_title="Dummy reminder 1",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    reminder_2 = new_reminder(
        reminder_id="def",
        user_id="test_user_1",
        reminder_title="Dummy reminder 2",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    reminder_3 = new_reminder(
        reminder_id="xxx",
        user_id="test_user_1",
        reminder_tags=["real"],
        reminder_title="Dummy reminder 3",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_3)

    with Client(app) as client:
        response = client.http.get("/reminders")
    returned_body = json.loads(response.body)
    assert isinstance(returned_body, list)
    assert len(returned_body) == 3
    reminder_ids_returned = [reminder["reminder_id"] for reminder in returned_body]
    assert sorted(reminder_ids_returned) == sorted(["abc", "def", "xxx"])


def test_view_list_of_reminders_filtered_by_tags(
    reminders_model, reminders, new_reminder, mocker
):
    """Test viewing filtered reminders by tags."""
    mocked_get_user_details = mocker.patch("app.get_user_details_from_context")
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )
    reminder_1 = new_reminder(
        reminder_id="abc",
        user_id="test_user_1",
        reminder_tags=["dummy"],
        reminder_title="Dummy reminder 1",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    reminder_2 = new_reminder(
        reminder_id="def",
        user_id="test_user_1",
        reminder_tags=["dummy"],
        reminder_title="Dummy reminder 2",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    reminder_3 = new_reminder(
        reminder_id="xxx",
        user_id="test_user_1",
        reminder_tags=["real"],
        reminder_title="Dummy reminder 3",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_3)
    with Client(app) as client:
        response = client.http.get("/reminders?tag=dummy")
    returned_body = json.loads(response.body)
    assert response.status_code == 200
    reminder_ids_returned = [reminder["reminder_id"] for reminder in returned_body]
    assert sorted(reminder_ids_returned) == sorted(["abc", "def"])
    assert "xxx" not in reminder_ids_returned


def test_get_remider_tags(reminders_model, reminders, new_reminder, mocker):
    """Test getting reminder tags."""
    mocked_get_user_details = mocker.patch(
        "chalicelib.utils.get_user_details_from_context"
    )
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )
    reminder_1 = new_reminder(
        reminder_id="abc",
        user_id="test_user_1",
        reminder_tags=["dummy"],
        reminder_title="Dummy reminder 1",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    reminder_2 = new_reminder(
        reminder_id="def",
        user_id="test_user_1",
        reminder_tags=["dummy"],
        reminder_title="Dummy reminder 2",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_2)
    reminder_3 = new_reminder(
        reminder_id="xxx",
        user_id="test_user_1",
        reminder_tags=["real"],
        reminder_title="Dummy reminder 3",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_3)
    with Client(app) as client:
        response = client.http.get("/tags")
    returned_body = json.loads(response.body)
    assert response.status_code == 200
    assert sorted(["dummy", "real"]) == sorted(returned_body)

    # Verify that get_user_details_from_context was called
    mocked_get_user_details.assert_called_once()


def test_get_details_about_a_reminder(reminders_model, reminders, new_reminder, mocker):
    """Test getting details about a specific reminder."""
    mocked_get_user_details = mocker.patch("app.get_user_details_from_context")
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )
    reminder_1 = new_reminder(
        reminder_id="abc",
        user_id="test_user_1",
        reminder_tags=["dummy"],
        reminder_title="Dummy reminder 1",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    with Client(app) as client:
        response = client.http.get("/reminders/abc")
    returned_body = json.loads(response.body)
    assert response.status_code == 200
    assert "reminder_description" in returned_body
    assert "next_reminder_date_time" in returned_body
    assert "should_expire" in returned_body
    assert returned_body["reminder_description"] == "Test reminder"


def test_delete_a_reminder(reminders_model, reminders, new_reminder, mocker):
    """Test deleting a reminder."""
    mocked_send_confirmation = mocker.patch("app.send_user_confirmation")
    mocked_get_user_details = mocker.patch("app.get_user_details_from_context")
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )
    reminder_1 = new_reminder(
        reminder_id="abc",
        user_id="test_user_1",
        reminder_tags=["dummy"],
        reminder_title="Dummy reminder 1",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    with Client(app) as client:
        response = client.http.delete("/reminders/abc")
    returned_body = json.loads(response.body)
    assert response.status_code == 200
    assert returned_body["message"] == "Reminder successfully deleted!"

    # Verify that send_user_confirmation was called with the correct arguments
    mocked_send_confirmation.assert_called_once()
    call_args = mocked_send_confirmation.call_args
    assert call_args[0][0] == "test_user_1"  # username
    assert "abc" in call_args[0][1]  # reminder_id in message
    assert "is deleted" in call_args[0][1]


def test_updating_a_reminder(reminders_model, reminders, new_reminder, mocker):
    """Test updating a reminder."""
    mocked_get_user_details = mocker.patch("app.get_user_details_from_context")
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )
    reminder_1 = new_reminder(
        reminder_id="abc",
        user_id="test_user_1",
        reminder_tags=["dummy"],
        reminder_title="Dummy reminder 1",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)
    changed_reminder = {
        "reminder_description": "Changed reminder",
        "reminder_expiration_date_time": (
            f"{datetime.strftime(datetime.now() + relativedelta(months=1), '%d/%m/%y')}"
            f" 10:00"
        ),
    }
    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))
    returned_body = json.loads(response.body)
    assert response.status_code == 200
    assert returned_body["message"] == "Reminder successfully updated!"
    reminder_from_db = list(
        dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
            reminder_id="abc", user_name="test_user_1"
        )
    )
    assert reminder_from_db[0].reminder_id == "abc"
    assert reminder_from_db[0].reminder_description == "Changed reminder"
