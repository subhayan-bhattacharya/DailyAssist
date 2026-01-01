"""Common utility functions for the reminders application."""

import datetime
import json
import logging
import traceback
import uuid

from fastapi import HTTPException
from core import data_structures
from core.backend.dynamodb.dynamo_backend import DynamoBackend
from core.lambda_handlers import filter_sns_arn_by_user
from core.lambda_handlers import send_reminder_message as _send_reminder_message
from pydantic import ValidationError


def send_user_confirmation(username, message):
    """Send confirmation message to user via SNS.

    Args:
        username: The username to send the confirmation to
        message: The message content to send
    """
    user_subscriptions = filter_sns_arn_by_user(username)
    for subscriber in user_subscriptions:
        _send_reminder_message(subscriber["topicArn"], message)


def share_reminder_with_user(
    reminder_id: str,
    share_request: data_structures.ShareReminderRequest,
    user_details: data_structures.UserDetails
) -> data_structures.MessageResponse:
    """Share a reminder with another user.

    Args:
        reminder_id: The ID of the reminder to share
        share_request: The share reminder request
        user_details: The user details from authentication

    Returns:
        MessageResponse: Response indicating success

    Raises:
        HTTPException: If sharing fails
    """
    try:
        original_user = user_details.user_name
        username_to_be_shared_with = share_request.username

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

        return data_structures.MessageResponse(message="Reminder successfully shared!")

    except HTTPException:
        raise
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail={"message": "Could not share the reminder!!", "error": str(error)}
        )


def create_new_reminder(
    create_request: data_structures.CreateReminderRequest,
    user_details: data_structures.UserDetails
) -> data_structures.CreateReminderResponse:
    """Create a new reminder in the database.

    Args:
        create_request: The create reminder request
        user_details: The user details from authentication

    Returns:
        CreateReminderResponse: Response with reminder ID and success message

    Raises:
        HTTPException: If creation fails
    """
    try:
        request_body = create_request.model_dump()
        request_body["reminder_frequency"] = data_structures.ReminderFrequency(
            request_body["reminder_frequency"]
        )

        reminder_details = data_structures.ReminderDetailsFromRequest.model_validate(
            request_body
        )

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

        return data_structures.CreateReminderResponse(
            reminderId=reminder_id,
            message="New reminder successfully created!"
        )

    except ValidationError as error:
        traceback.print_exc()
        # This is a hack to get the error message string in pydantic
        error_message = str(error)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Could not create a new reminder!!",
                "error": error_message,
            }
        )
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail={"message": "Could not create a new reminder!!", "error": str(error)}
        )


def get_all_tags_for_user(user_details: data_structures.UserDetails) -> list[str]:
    """Get all reminder tags for a user.

    Args:
        user_details: The user details from authentication

    Returns:
        list[str]: List of unique tags

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        all_reminder_details = DynamoBackend.get_all_reminders_for_a_user(
            user_id=user_details.user_name
        )
        tags = []
        for reminder in all_reminder_details:
            tags.append(list(reminder.reminder_tags)[0])
        return list(set(tags))

    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail={"message": "Could not retrieve all tags!!", "error": str(error)}
        )


def get_all_reminders_for_user(
    user_details: data_structures.UserDetails,
    tag: str | None = None
) -> list[data_structures.AllRemindersPerUser]:
    """Get all reminders for a user, optionally filtered by tag.

    Args:
        user_details: The user details from authentication
        tag: Optional tag to filter reminders

    Returns:
        list[AllRemindersPerUser]: List of reminders

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        if tag is not None:
            logging.info(f"Tag name provided is {tag}")
            all_reminder_details = DynamoBackend.get_all_reminders_for_a_user_by_tag(
                user_id=user_details.user_name, tag=tag
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

        return sorted_reminders_per_user

    except ValidationError as error:
        traceback.print_exc()
        # This is a hack to get the error message string in pydantic
        error_message = str(error)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Could not retrieve all reminders!!",
                "error": error_message,
            }
        )
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail={"message": "Could not retrieve all reminders!!", "error": str(error)}
        )


def view_reminder_details_for_user(
    reminder_id: str,
    user_details: data_structures.UserDetails
) -> data_structures.SingleReminder:
    """View the details of a reminder for the user making the request.

    Args:
        reminder_id: The ID of the reminder to view
        user_details: The user details from authentication

    Returns:
        SingleReminder: Reminder details

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        single_reminder_details = DynamoBackend.get_a_reminder_for_a_user(
            reminder_id=reminder_id, user_name=user_details.user_name
        )
        if len(single_reminder_details) == 0:
            raise ValueError(f"No such reminder with id: {reminder_id}")
        return data_structures.SingleReminder.model_validate(
            single_reminder_details[0].attribute_values
        )
    except ValidationError as error:
        traceback.print_exc()
        # This is a hack to get the error message string in pydantic
        error_message = str(error)
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    f"Could not retrieve reminder with reminder id "
                    f"{reminder_id}!!"
                ),
                "error": error_message,
            }
        )
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    f"Could not retrieve reminder with reminder id "
                    f"{reminder_id}!!"
                ),
                "error": str(error),
            }
        )


def delete_reminder_for_user(
    reminder_id: str,
    user_details: data_structures.UserDetails
) -> data_structures.ReminderIdResponse:
    """Delete a reminder for the user making the request.

    Args:
        reminder_id: The ID of the reminder to delete
        user_details: The user details from authentication

    Returns:
        ReminderIdResponse: Response with reminder ID and success message

    Raises:
        HTTPException: If deletion fails
    """
    try:
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

        return data_structures.ReminderIdResponse(
            reminderId=reminder_id,
            message="Reminder successfully deleted!"
        )
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Could not delete reminder {reminder_id}!!",
                "error": str(error),
            }
        )


def update_reminder_for_user(
    reminder_id: str,
    update_request: data_structures.UpdateReminderRequest,
    user_details: data_structures.UserDetails
) -> data_structures.ReminderIdResponse:
    """Update a reminder for the user making the request.

    Args:
        reminder_id: The ID of the reminder to update
        update_request: The update reminder request
        user_details: The user details from authentication

    Returns:
        ReminderIdResponse: Response with reminder ID and success message

    Raises:
        HTTPException: If update fails
    """
    try:
        username = user_details.user_name
        request_body = update_request.model_dump(exclude_none=True)
        exisiting_reminder_in_database = DynamoBackend.get_a_reminder_for_a_user(
            reminder_id=reminder_id, user_name=username
        )
        if len(exisiting_reminder_in_database) == 0:
            raise ValueError(f"No such reminder with id: {reminder_id}")
        existing_reminder = exisiting_reminder_in_database[0]
        updated_reminder = {
            **existing_reminder.attribute_values,
            **request_body,
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

        return data_structures.ReminderIdResponse(
            reminderId=reminder_id,
            message="Reminder successfully updated!"
        )
    except ValidationError as error:
        traceback.print_exc()
        # This is a hack to get the error message string in pydantic
        error_message = str(error)
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Could not update reminder {reminder_id}!!",
                "error": error_message,
            }
        )
    except Exception as error:
        traceback.print_exc()
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Could not update reminder {reminder_id}!!",
                "error": str(error),
            }
        )
