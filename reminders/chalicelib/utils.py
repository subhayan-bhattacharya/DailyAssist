"""Common utility functions for the reminders application."""

import datetime
import json
import logging
import traceback
import uuid

from chalice import Response
from chalicelib import data_structures
from chalicelib.backend.dynamodb.dynamo_backend import DynamoBackend
from chalicelib.lambda_handlers import filter_sns_arn_by_user
from chalicelib.lambda_handlers import send_reminder_message as _send_reminder_message
from pydantic import ValidationError


def get_user_details_from_context(request_context):
    """Extract user details from the request context.

    Args:
        request_context: The request context containing authorization claims

    Returns:
        UserDetails: User details object with username and email
    """
    user_details = data_structures.UserDetails(
        user_name=request_context["authorizer"]["claims"]["cognito:username"],
        user_email=request_context["authorizer"]["claims"]["email"],
    )
    return user_details


def send_user_confirmation(username, message):
    """Send confirmation message to user via SNS.

    Args:
        username: The username to send the confirmation to
        message: The message content to send
    """
    user_subscriptions = filter_sns_arn_by_user(username)
    for subscriber in user_subscriptions:
        _send_reminder_message(subscriber["topicArn"], message)


def share_reminder_with_user(reminder_id: str, current_request, request_context):
    """Share a reminder with another user.

    Args:
        reminder_id: The ID of the reminder to share
        current_request: The current Chalice request object
        request_context: The request context containing user details

    Returns:
        Response: JSON response indicating success or failure
    """
    try:
        user_details = get_user_details_from_context(request_context)
        original_user = user_details.user_name
        request_body = json.loads(current_request.raw_body.decode())
        username_to_be_shared_with = request_body.get("username")

        if username_to_be_shared_with is None:
            return Response(
                body=json.dumps(
                    {
                        "message": "Could not share the reminder!!",
                        "error": (
                            "The message body needs to contain the username "
                            "with whom the reminder needs to be shared!"
                        ),
                    },
                ),
                status_code=400,
                headers={"Content-Type": "application/json"},
            )

        existing_reminder = data_structures.SingleReminder.model_validate(
            DynamoBackend.get_a_reminder_for_a_user(
                reminder_id=reminder_id, user_name=original_user
            )[0].attribute_values
        )
        existing_reminder.user_id = username_to_be_shared_with
        DynamoBackend.create_a_new_reminder(existing_reminder)

        # Send confirmation message to the user when the reminder is created
        user_readable_expiration_date = (
            existing_reminder.reminder_expiration_date_time.strftime("%d/%m/%y %H:%M")
        )
        message = (
            f"Reminder shared with user: {username_to_be_shared_with}."
            f"Reminder Details : {existing_reminder.reminder_description}. "
            f"Expiration date : {user_readable_expiration_date}"
        )
        send_user_confirmation(original_user, message)

    except Exception as error:
        traceback.print_exc()
        return Response(
            body=json.dumps(
                {"message": "Could not share the reminder!!", "error": str(error)},
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )

    return Response(
        body=json.dumps({"message": "Reminder successfully shared!"}),
        status_code=200,
        headers={"Content-Type": "application/json"},
    )


def create_new_reminder(current_request, request_context):
    """Create a new reminder in the database.

    Args:
        current_request: The current Chalice request object
        request_context: The request context containing user details

    Returns:
        Response: JSON response indicating success or failure
    """
    try:
        request_body = json.loads(current_request.raw_body.decode())
        request_body["reminder_frequency"] = data_structures.ReminderFrequency(
            request_body["reminder_frequency"]
        )

        reminder_details = data_structures.ReminderDetailsFromRequest.model_validate(
            request_body
        )

        user_details = get_user_details_from_context(request_context)
        username = user_details.user_name
        # Check if the user has already created a similar entry by querying the GSI
        reminders_present = list(
            DynamoBackend.get_a_reminder_gsi(username, reminder_details.reminder_title)
        )
        if len(reminders_present) > 0:
            logging.error(f"There are reminders present {reminders_present}")
            raise ValueError(
                f"There is already a reminder with name "
                f"{reminder_details.reminder_title} for user {username}"
            )

        reminder_id = str(uuid.uuid1())

        reminder_details_as_dict = reminder_details.model_dump()
        reminder_details_as_dict["reminder_frequency"] = reminder_details_as_dict[
            "reminder_frequency"
        ].value

        new_reminder = data_structures.SingleReminder.model_validate(
            {
                **reminder_details_as_dict,
                **{
                    "reminder_id": reminder_id,
                    "reminder_creation_time": datetime.datetime.now(),
                    "user_id": username,
                },
            }
        )

        DynamoBackend.create_a_new_reminder(new_reminder=new_reminder)
        # Send confirmation message to the user when the reminder is created
        user_readable_expiration_date = (
            reminder_details.reminder_expiration_date_time.strftime("%d/%m/%y %H:%M")
        )
        message = (
            f"New reminder added for date : {user_readable_expiration_date}."
            f"Reminder Details : {reminder_details.reminder_description}"
        )
        send_user_confirmation(username, message)

        return Response(
            body=json.dumps(
                {
                    "reminderId": reminder_id,
                    "message": "New reminder successfully created!",
                }
            ),
            status_code=201,
            headers={"Content-Type": "application/json"},
        )

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


def get_all_tags_for_user(request_context):
    """Get all reminder tags for a user.

    Args:
        request_context: The request context containing user details

    Returns:
        list or Response: List of tags on success, Response object on error
    """
    try:
        user_details = get_user_details_from_context(request_context)
        all_reminder_details = DynamoBackend.get_all_reminders_for_a_user(
            user_id=user_details.user_name
        )
        tags = []
        for reminder in all_reminder_details:
            tags.append(list(reminder.reminder_tags)[0])
        return list(set(tags))

    except Exception as error:
        traceback.print_exc()
        return Response(
            body=json.dumps(
                {"message": "Could not retrieve all tags!!", "error": str(error)},
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )
