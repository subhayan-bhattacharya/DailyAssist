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
    assert (
        new_reminder_request["reminder_expiration_date_time"] in call_args[0][1]
    )  # expiration date in message
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
    mocked_get_user_details = mocker.patch(
        "chalicelib.utils.get_user_details_from_context"
    )
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
    mocked_send_confirmation = mocker.patch("chalicelib.utils.send_user_confirmation")
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


def test_updating_nonexistent_reminder(reminders_model, reminders, mocker):
    """Test updating a reminder that doesn't exist."""
    mocked_get_user_details = mocker.patch(
        "chalicelib.utils.get_user_details_from_context"
    )
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )

    changed_reminder = {
        "reminder_description": "Changed reminder",
        "reminder_expiration_date_time": (
            f"{datetime.strftime(datetime.now() + relativedelta(months=1), '%d/%m/%y')}"
            f" 10:00"
        ),
    }

    with Client(app) as client:
        response = client.http.put(
            "/reminders/nonexistent", body=json.dumps(changed_reminder)
        )

    returned_body = json.loads(response.body)
    assert response.status_code == 400
    assert "Could not update reminder nonexistent!!" in returned_body["message"]
    assert "No such reminder with id: nonexistent" in returned_body["error"]


def test_updating_reminder_with_invalid_json(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with invalid JSON in request body."""
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

    # Invalid JSON string
    invalid_json = '{"reminder_description": "Changed reminder", "invalid": }'

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=invalid_json)

    returned_body = json.loads(response.body)
    assert response.status_code == 400
    assert "Could not update reminder abc!!" in returned_body["message"]


def test_updating_reminder_with_empty_title(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with empty title (should fail validation)."""
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

    changed_reminder = {
        "reminder_title": "",  # Empty title should fail validation
        "reminder_description": "Changed reminder",
    }

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))

    returned_body = json.loads(response.body)
    assert response.status_code == 400
    assert "Could not update reminder abc!!" in returned_body["message"]
    assert "Title cannot be empty" in returned_body["error"]


def test_updating_reminder_with_whitespace_only_title(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with whitespace-only title (should fail validation)."""
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

    changed_reminder = {
        "reminder_title": "   ",  # Whitespace-only title should fail validation
        "reminder_description": "Changed reminder",
    }

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))

    returned_body = json.loads(response.body)
    assert response.status_code == 400
    assert "Could not update reminder abc!!" in returned_body["message"]
    assert "Title cannot be empty" in returned_body["error"]


def test_updating_reminder_with_invalid_date_format(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with invalid date format."""
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

    changed_reminder = {
        "reminder_description": "Changed reminder",
        "reminder_expiration_date_time": "invalid-date-format",
    }

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))

    returned_body = json.loads(response.body)
    assert response.status_code == 400
    assert "Could not update reminder abc!!" in returned_body["message"]


def test_updating_reminder_with_invalid_frequency(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with invalid frequency."""
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

    changed_reminder = {
        "reminder_description": "Changed reminder",
        "reminder_frequency": "invalid_frequency",
    }

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))

    returned_body = json.loads(response.body)
    assert response.status_code == 400
    assert "Could not update reminder abc!!" in returned_body["message"]


def test_updating_reminder_frequency_change(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder's frequency successfully."""
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

    changed_reminder = {
        "reminder_frequency": "daily",
        "reminder_description": "Updated to daily reminder",
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
    assert reminder_from_db[0].reminder_frequency == "daily"
    assert reminder_from_db[0].reminder_description == "Updated to daily reminder"


def test_updating_reminder_with_next_reminder_date(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with explicit next_reminder_date_time."""
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

    next_date = datetime.now() + relativedelta(days=5)
    changed_reminder = {
        "reminder_description": "Changed reminder",
        "next_reminder_date_time": f"{datetime.strftime(next_date, '%d/%m/%y')} 15:00",
    }

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))

    returned_body = json.loads(response.body)
    assert response.status_code == 200
    assert returned_body["message"] == "Reminder successfully updated!"


def test_updating_reminder_should_expire_toggle(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder's should_expire flag."""
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

    changed_reminder = {
        "reminder_frequency": "monthly",
        "should_expire": False,
        "reminder_description": "Now non-expiring reminder",
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
    assert reminder_from_db[0].should_expire is False


def test_updating_reminder_tags(reminders_model, reminders, new_reminder, mocker):
    """Test updating a reminder's tags."""
    mocked_get_user_details = mocker.patch(
        "chalicelib.utils.get_user_details_from_context"
    )
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )

    reminder_1 = new_reminder(
        reminder_id="abc",
        user_id="test_user_1",
        reminder_tags=["old_tag"],
        reminder_title="Dummy reminder 1",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)

    changed_reminder = {
        "reminder_tags": ["new_tag", "another_tag"],
        "reminder_description": "Updated tags",
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
    assert set(reminder_from_db[0].reminder_tags) == {"new_tag", "another_tag"}


def test_updating_reminder_partial_update(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating only one field of a reminder (partial update)."""
    mocked_get_user_details = mocker.patch(
        "chalicelib.utils.get_user_details_from_context"
    )
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )

    reminder_1 = new_reminder(
        reminder_id="abc",
        user_id="test_user_1",
        reminder_tags=["original_tag"],
        reminder_title="Original Title",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)

    # Only update description, leave everything else unchanged
    changed_reminder = {
        "reminder_description": "Only description changed",
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
    # Description should be updated
    assert reminder_from_db[0].reminder_description == "Only description changed"
    # Other fields should remain unchanged
    assert reminder_from_db[0].reminder_title == "Original Title"
    assert set(reminder_from_db[0].reminder_tags) == {"original_tag"}


def test_updating_reminder_with_past_expiration_date(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with past expiration date (should fail)."""
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

    # Set expiration date to yesterday
    past_date = datetime.now() - relativedelta(days=1)
    reminder_expiration_date_time = f"{datetime.strftime(past_date, '%d/%m/%y')} 10:00"
    changed_reminder = {
        "reminder_description": "Changed reminder",
        "reminder_expiration_date_time": reminder_expiration_date_time,
    }

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))

    returned_body = json.loads(response.body)
    assert response.status_code == 400
    assert "Could not update reminder abc!!" in returned_body["message"]


def test_updating_reminder_with_malformed_request_body(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with completely malformed request body."""
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

    # Completely invalid request body - not even valid JSON structure for a reminder
    with Client(app) as client:
        response = client.http.put("/reminders/abc", body="not-json-at-all")

    returned_body = json.loads(response.body)
    assert response.status_code == 400
    assert "Could not update reminder abc!!" in returned_body["message"]


def test_updating_reminder_with_empty_tags_list(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with empty tags list."""
    mocked_get_user_details = mocker.patch(
        "chalicelib.utils.get_user_details_from_context"
    )
    mocked_get_user_details.return_value = data_structures.UserDetails(
        user_name="test_user_1", user_email="test@gmail.com"
    )

    reminder_1 = new_reminder(
        reminder_id="abc",
        user_id="test_user_1",
        reminder_tags=["original_tag"],
        reminder_title="Dummy reminder 1",
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder_1)

    changed_reminder = {
        "reminder_tags": [],  # Empty tags list
        "reminder_description": "Updated tags to empty",
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
    assert len(reminder_from_db[0].reminder_tags) == 0


def test_updating_reminder_with_once_frequency_no_expiration(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder to 'once' frequency without expiration date."""
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

    changed_reminder = {
        "reminder_frequency": "once",
        "should_expire": False,  # This conflicts with 'once' frequency
        "reminder_description": "Changed to once without expiration",
    }

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))

    returned_body = json.loads(response.body)
    assert response.status_code == 400
    assert "Could not update reminder abc!!" in returned_body["message"]
    assert "Expiration date required for one-time reminders" in returned_body["error"]


def test_updating_reminder_with_extremely_long_title(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with extremely long title."""
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

    # Extremely long title (1000+ characters)
    long_title = "A" * 1000
    changed_reminder = {
        "reminder_title": long_title,
        "reminder_description": "Testing extremely long title",
    }

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))

    returned_body = json.loads(response.body)
    # This should succeed (no length validation in current model)
    assert response.status_code == 200
    assert returned_body["message"] == "Reminder successfully updated!"

    reminder_from_db = list(
        dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
            reminder_id="abc", user_name="test_user_1"
        )
    )
    assert reminder_from_db[0].reminder_title == long_title


def test_updating_reminder_with_special_characters_in_fields(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder with special characters in various fields."""
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

    # Special characters and emojis
    changed_reminder = {
        "reminder_title": "Test with émojis 🚀 & spéciàl chars!",
        "reminder_description": "Description with 中文 and symbols: @#$%^&*()",
        "reminder_tags": ["spëcîäl-tag", "emoji🏷️", "symbols@#$"],
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
    assert reminder_from_db[0].reminder_title == "Test with émojis 🚀 & spéciàl chars!"


def test_updating_reminder_concurrent_update_scenario(
    reminders_model, reminders, new_reminder, mocker
):
    """Test updating a reminder that might have been modified by another process."""
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

    # Simulate concurrent update by modifying the reminder in DB directly
    reminder_1.reminder_description = "Modified by another process"
    dynamo_backend.DynamoBackend.update_a_reminder(
        reminder_id="abc",
        updated_reminder={"reminder_description": "Modified by another process"},
    )

    # Now try to update with our process
    changed_reminder = {
        "reminder_description": "Our process update",
        "reminder_title": "Updated title",
    }

    with Client(app) as client:
        response = client.http.put("/reminders/abc", body=json.dumps(changed_reminder))

    returned_body = json.loads(response.body)
    assert response.status_code == 200
    assert returned_body["message"] == "Reminder successfully updated!"

    # The latest update should win (no optimistic locking currently)
    reminder_from_db = list(
        dynamo_backend.DynamoBackend.get_a_reminder_for_a_user(
            reminder_id="abc", user_name="test_user_1"
        )
    )
    assert reminder_from_db[0].reminder_description == "Our process update"
    assert reminder_from_db[0].reminder_title == "Updated title"
