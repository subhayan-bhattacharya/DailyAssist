import datetime
import json
import logging
import os
import traceback
import uuid

from chalice import Chalice, CognitoUserPoolAuthorizer, Response
from pydantic import ValidationError

from chalicelib import data_structures
from chalicelib.backend.dynamodb.dynamo_backend import DynamoBackend

app = Chalice(app_name="daily_assist_reminders")


authorizer = CognitoUserPoolAuthorizer(
    os.getenv("COGNITO_USER_POOL_NAME"),
    provider_arns=[os.getenv("COGNITO_USER_POOL_ARN")],
)


@app.route(
    "/reminders",
    methods=["POST"],
    content_types=["application/json"],
    authorizer=authorizer,
)
def create_a_new_reminder():
    """Creates a new reminder in the database."""
    try:
        request_context = app.current_request.context
        request_body = json.loads(app.current_request.raw_body.decode())
        request_body["reminder_frequency"] = data_structures.ReminderFrequency[
            request_body["reminder_frequency"]
        ]

        reminder_details = data_structures.ReminderDetailsFromRequest.parse_obj(
            request_body
        )

        user_details = data_structures.UserDetails(
            user_name=request_context["authorizer"]["claims"]["cognito:username"],
            user_email=request_context["authorizer"]["claims"]["email"],
        )
        # Check if the user has already created a similar entry by querying the GSI
        reminders_present = list(
            DynamoBackend.get_a_reminder_gsi(
                user_details.user_name, reminder_details.reminder_title
            )
        )
        if len(reminders_present) > 0:
            logging.error(f"There are reminders present {reminders_present}")
            raise ValueError(
                f"There is already a reminder with name {reminder_details.reminder_title}"
                f" for user {user_details.user_name}"
            )

        reminder_id = str(uuid.uuid1())

        reminder_details_as_dict = reminder_details.dict()
        reminder_details_as_dict["reminder_frequency"] = reminder_details_as_dict["reminder_frequency"].value
        new_reminder = data_structures.NewReminder.parse_obj(
            {
                **{
                    "reminder_id": reminder_id,
                    "reminder_creation_time": datetime.datetime.now(),
                    "user_id": user_details.user_name
                },
                **reminder_details_as_dict,
            }
        )

        DynamoBackend.create_a_new_reminder(new_reminder=new_reminder)
    except ValidationError as error:
        traceback.print_exc()
        # This is a hack to get the error message string in pydantic
        error_message = str(error.raw_errors[0].exc)
        return Response(
            body=json.dumps(
                {
                    "message": "Could not create a new reminder!!",
                    "error": error_message,
                },
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )
    except Exception as error:
        traceback.print_exc()
        return Response(
            body=json.dumps(
                {"message": "Could not create a new reminder!!", "error": str(error)},
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )
    return Response(
        body=json.dumps({"message": "New reminder successfully created!"}),
        status_code=201,
        headers={"Content-Type": "application/json"},
    )


@app.route(
    "/reminders",
    methods=["GET"],
    authorizer=authorizer,
)
def get_all_reminders_for_a_user():
    """Gets the list of all reminders for a user."""
    try:
        request_context = app.current_request.context
        user_details = data_structures.UserDetails(
            user_name=request_context["authorizer"]["claims"]["cognito:username"],
            user_email=request_context["authorizer"]["claims"]["email"],
        )
        all_reminder_details = DynamoBackend.get_all_reminders_for_a_user(user_id=user_details.user_name)
        return [
            json.loads(data_structures.AllRemindersPerUser.parse_obj(reminder.attribute_values).json())
            for reminder in all_reminder_details
        ]
    except ValidationError as error:
        traceback.print_exc()
        # This is a hack to get the error message string in pydantic
        error_message = str(error.raw_errors[0].exc)
        return Response(
            body=json.dumps(
                {
                    "message": "Could not retrieve all reminders!!",
                    "error": error_message,
                },
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )
    except Exception as error:
        traceback.print_exc()
        return Response(
            body=json.dumps(
                {"message": "Could not retrieve all reminders!!", "error": str(error)},
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )
