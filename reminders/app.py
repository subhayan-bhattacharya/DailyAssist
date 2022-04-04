import json
import uuid

from chalice import Chalice, Response
from chalice import CognitoUserPoolAuthorizer
from chalicelib.backend.dynamodb.dynamo_backend import DynamoBackend
from chalicelib import data_structures
import os
import datetime
import logging
import traceback

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
        reminders_present = list(DynamoBackend.get_a_reminder_gsi(user_details.user_name, reminder_details.reminder_title))
        if len(reminders_present) > 0:
            logging.error(f"There are reminders present {reminders_present}")
            raise ValueError(f"There is already a reminder with {reminder_details.reminder_title}"
                             f" for user {user_details.user_name}")

        reminder_id = str(uuid.uuid1())
        new_reminder = data_structures.NewReminder(
            reminder_id=reminder_id,
            user_id=user_details.user_name,
            reminder_title=reminder_details.reminder_title,
            reminder_description=reminder_details.reminder_description,
            reminder_tags=reminder_details.reminder_tags,
            reminder_frequency=reminder_details.reminder_frequency.value,
            should_expire=reminder_details.should_expire,
            reminder_expiration_date_time=reminder_details.reminder_expiration_date_time,
            next_reminder_date_time=reminder_details.next_reminder_date_time,
            reminder_creation_time=datetime.datetime.now(),
        )
        DynamoBackend.create_a_new_reminder(new_reminder=new_reminder)
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


@app.route("/reminders", methods=["GET"], authorizer=authorizer)
def get_all_reminders():
    """Get all the reminders create or shared by user."""
    pass
