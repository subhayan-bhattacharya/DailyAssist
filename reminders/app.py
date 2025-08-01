"""Main Chalice application for daily assist reminders service."""

import json
import logging
import os
import traceback

from chalice import Chalice, CognitoUserPoolAuthorizer, Response
from chalicelib import data_structures
from chalicelib.backend.dynamodb.dynamo_backend import DynamoBackend
from chalicelib.lambda_handlers import (
    delete_expired_reminders,
    query_and_send_reminders,
)
from chalicelib.utils import (
    create_new_reminder,
    get_all_tags_for_user,
    get_user_details_from_context,
    send_user_confirmation,
    share_reminder_with_user,
)
from pydantic import ValidationError

app = Chalice(app_name="daily_assist_reminders")


authorizer = CognitoUserPoolAuthorizer(
    os.getenv("COGNITO_USER_POOL_NAME"),
    provider_arns=[os.getenv("COGNITO_USER_POOL_ARN")],
)


@app.lambda_function(name="queryAndSendReminders")
def lambda_query_and_send_reminders(event, context):
    """Lambda function to query and send reminders."""
    return query_and_send_reminders(event, context)


@app.lambda_function(name="deleteExpiredReminders")
def lambda_delete_expired_reminders(event, context):
    """Lambda function to delete expired reminders."""
    return delete_expired_reminders(event, context)


@app.route("/reminders/{reminder_id}", methods=["POST"], authorizer=authorizer)
def share_a_reminder_with_someone(reminder_id: str):
    """Try to share a reminder with someone."""
    return share_reminder_with_user(
        reminder_id, app.current_request, app.current_request.context
    )


@app.route(
    "/reminders",
    methods=["POST"],
    content_types=["application/json"],
    authorizer=authorizer,
)
def create_a_new_reminder():
    """Creates a new reminder in the database."""
    return create_new_reminder(app.current_request, app.current_request.context)


@app.route(
    "/tags",
    methods=["GET"],
    authorizer=authorizer,
)
def get_all_tags_for_a_user():
    """Gets the list of all reminder tags currenty in the database."""
    return get_all_tags_for_user(app.current_request.context)


@app.route(
    "/reminders",
    methods=["GET"],
    authorizer=authorizer,
)
def get_all_reminders_for_a_user():
    """Gets the list of all reminders for a user."""
    try:
        request_context = app.current_request.context
        user_details = get_user_details_from_context(request_context)
        if app.current_request.query_params is not None:
            tag_name = app.current_request.query_params.get("tag")
            logging.info(f"Tag name provided is {tag_name}")
            if tag_name is not None:
                all_reminder_details = (
                    DynamoBackend.get_all_reminders_for_a_user_by_tag(
                        user_id=user_details.user_name, tag=tag_name
                    )
                )
            else:
                logging.info("The tag name is None... hence getting all reminders")
                all_reminder_details = DynamoBackend.get_all_reminders_for_a_user(
                    user_id=user_details.user_name
                )
        else:
            logging.info("No tag provided... getting all reminders for the user...")
            all_reminder_details = DynamoBackend.get_all_reminders_for_a_user(
                user_id=user_details.user_name
            )
        logging.debug(all_reminder_details)
        all_reminders_per_user = [
            data_structures.AllRemindersPerUser.model_validate(
                reminder.attribute_values
            )
            for reminder in all_reminder_details
        ]
        sorted_reminders_per_user = sorted(
            all_reminders_per_user, key=lambda x: x.reminder_expiration_date_time
        )

        return [
            json.loads(reminder.model_dump_json())
            for reminder in sorted_reminders_per_user
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


@app.route("/reminders/{reminder_id}", methods=["GET"], authorizer=authorizer)
def view_details_of_a_reminder_for_a_user(reminder_id: str):
    """View the details of a reminder for the user making the request."""
    try:
        request_context = app.current_request.context
        user_details = get_user_details_from_context(request_context)
        single_reminder_details = DynamoBackend.get_a_reminder_for_a_user(
            reminder_id=reminder_id, user_name=user_details.user_name
        )
        if len(single_reminder_details) == 0:
            raise ValueError(f"No such reminder with id: {reminder_id}")
        return json.loads(
            data_structures.SingleReminder.model_validate(
                single_reminder_details[0].attribute_values
            ).model_dump_json()
        )
    except ValidationError as error:
        traceback.print_exc()
        # This is a hack to get the error message string in pydantic
        error_message = str(error.raw_errors[0].exc)
        return Response(
            body=json.dumps(
                {
                    "message": (
                        f"Could not retrieve reminder with reminder id "
                        f"{reminder_id}!!"
                    ),
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
                {
                    "message": (
                        f"Could not retrieve reminder with reminder id "
                        f"{reminder_id}!!"
                    ),
                    "error": str(error),
                },
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )


@app.route("/reminders/{reminder_id}", methods=["DELETE"], authorizer=authorizer)
def delete_a_reminder(reminder_id: str):
    """Delete a reminder."""
    try:
        request_context = app.current_request.context
        user_details = get_user_details_from_context(request_context)
        username = user_details.user_name
        single_reminder_details = DynamoBackend.get_a_reminder_for_a_user(
            reminder_id=reminder_id, user_name=user_details.user_name
        )
        if len(single_reminder_details) == 0:
            raise ValueError(
                f"No reminder with reminder id: {reminder_id} exists for {username}"
            )
        DynamoBackend.delete_a_reminder(reminder_id=reminder_id)
        # We also want to send a confirmation message to the user
        # when the reminder is deleted.
        # However there is a catch
        message = (
            f"Reminder id : {single_reminder_details[0].reminder_id} "
            f"with details : {single_reminder_details[0].reminder_description} "
            f"is deleted."
        )
        send_user_confirmation(username, message)
    except Exception as error:
        traceback.print_exc()
        return Response(
            body=json.dumps(
                {
                    "message": f"Could not delete reminder {reminder_id}!!",
                    "error": str(error),
                },
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )
    return Response(
        body=json.dumps(
            {"reminderId": reminder_id, "message": "Reminder successfully deleted!"}
        ),
        status_code=200,
        headers={"Content-Type": "application/json"},
    )


@app.route("/reminders/{reminder_id}", methods=["PUT"], authorizer=authorizer)
def update_a_reminder(reminder_id: str):
    """Update a reminder with the given reminder id."""
    try:
        request_context = app.current_request.context
        user_details = get_user_details_from_context(request_context)
        username = user_details.user_name
        request_body = json.loads(app.current_request.raw_body.decode())
        exisiting_reminder_in_database = DynamoBackend.get_a_reminder_for_a_user(
            reminder_id=reminder_id, user_name=username
        )
        if len(exisiting_reminder_in_database) == 0:
            raise ValueError(f"No such reminder with id: {reminder_id}")
        existing_reminder = exisiting_reminder_in_database[0]
        updated_reminder = {
            **existing_reminder.attribute_values,
            **request_body,
            "reminder_frequency": data_structures.ReminderFrequency(
                existing_reminder.reminder_frequency
            ),
        }
        # First case we are just updating the expiration date of a request and not
        # updating the next reminder date in that case we need this to be calculated
        # again hence we need to pop this value. But if it is given in the request
        # body then we do not need to calculate it hence no need to pop
        if updated_reminder.get("next_reminder_date_time") and not request_body.get(
            "next_reminder_date_time"
        ):
            updated_reminder.pop("next_reminder_date_time")
        reminder_details = data_structures.ReminderDetailsFromRequest.model_validate(
            updated_reminder
        )
        reminder_details_as_dict = reminder_details.model_dump()
        reminder_details_as_dict["reminder_frequency"] = reminder_details_as_dict[
            "reminder_frequency"
        ].value
        DynamoBackend.update_a_reminder(
            reminder_id=reminder_id, updated_reminder=reminder_details_as_dict
        )
    except ValidationError as error:
        traceback.print_exc()
        # This is a hack to get the error message string in pydantic
        error_message = str(error.raw_errors[0].exc)
        return Response(
            body=json.dumps(
                {
                    "message": f"Could not update reminder {reminder_id}!!",
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
                {
                    "message": f"Could not update reminder {reminder_id}!!",
                    "error": str(error),
                },
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )
    return Response(
        body=json.dumps(
            {"reminderId": reminder_id, "message": "Reminder successfully updated!"}
        ),
        status_code=200,
        headers={"Content-Type": "application/json"},
    )
