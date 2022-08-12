import json
from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta

from app import app
from chalicelib.backend.dynamodb import dynamo_backend


@pytest.fixture()
def new_reminder_request():
    """Create a dummy new reminder request."""
    return {
        "reminder_title": "Dummy reminder",
        "reminder_description": "Description",
        "reminder_tags": ["doctor"],
        "reminder_frequency": "once",
        "should_expire": True,
        "reminder_expiration_date_time": f"{datetime.strftime(datetime.now() + relativedelta(months=1), '%d/%m/%y')}"
        f" 10:00",
        "reminder_id": "6850f2e9-f920-11ec-a7c5-416944df2ab7",
    }


@pytest.fixture
def create_event():
    def create_event_inner(
        uri, method, path, body, request_context, content_type="application/json"
    ):
        full_request_context = {
            **request_context,
            **{
                "httpMethod": method,
                "resourcePath": uri,
            },
        }
        return {
            "requestContext": full_request_context,
            "headers": {
                "Content-Type": content_type,
            },
            "pathParameters": path,
            "queryStringParameters": {},
            "multiValueQueryStringParameters": {},
            "body": body,
            "stageVariables": {},
        }

    return create_event_inner


def test_create_a_new_reminder_normal_use_case(
    reminders_model, reminders, new_reminder_request, create_event
):
    """Test the function create a new reminder from app."""
    # We check first that there is nothing in the db for this user and reminder title
    reminder_from_db = dynamo_backend.DynamoBackend.get_a_reminder_gsi(
        user_id="Test user", reminder_title=new_reminder_request["reminder_title"]
    )
    assert len(list(reminder_from_db)) == 0

    event = create_event(
        uri="/reminders",
        method="POST",
        path={},
        body=json.dumps(new_reminder_request),
        request_context={
            "authorizer": {
                "claims": {
                    "cognito:username": "Test user",
                    "email": "test_user@email.com",
                }
            }
        },
    )
    response = app(event, context=None)
    assert response["statusCode"] == 201
    assert json.loads(response["body"]) == {
        "message": "New reminder successfully created!"
    }

    # We check if the new reminder is really created
    # We just use our database methods to test the backend
    reminder_from_db = list(
        dynamo_backend.DynamoBackend.get_a_reminder_gsi(
            user_id="Test user", reminder_title=new_reminder_request["reminder_title"]
        )
    )
    assert len(reminder_from_db) == 1
    assert reminder_from_db[0].reminder_id == new_reminder_request["reminder_id"]


def test_share_a_reminder(
    reminders_model, reminders, new_reminder_request, create_event, new_reminder
):
    """Share a reminder with another user."""
    # First create a new reminder in db.
    reminder = new_reminder(
        reminder_id=new_reminder_request["reminder_id"],
        user_id="test_user_1",
        reminder_title=new_reminder_request["reminder_title"],
    )
    dynamo_backend.DynamoBackend.create_a_new_reminder(reminder)

    new_reminder_request["user_name"] = "test_user_2"

    event = create_event(
        uri="/reminders",
        method="POST",
        path={},
        body=json.dumps(new_reminder_request),
        request_context={
            "authorizer": {
                "claims": {
                    "cognito:username": "test_user_1",
                    "email": "test_user_1@email.com",
                }
            }
        },
    )

    response = app(event, context=None)
    assert response["statusCode"] == 201
    assert json.loads(response["body"]) == {
        "message": "New reminder successfully created!"
    }

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
