"""Lambda handler functions for reminders service."""

import datetime
import logging

import boto3
from chalicelib import data_structures
from chalicelib.backend.dynamodb.dynamo_backend import DynamoBackend


def get_reminder_description_for_reminders_for_today(user):
    """Get the reminder description from the database for today's reminders."""
    all_reminders_for_a_user = DynamoBackend.get_all_reminders_for_a_user(user_id=user)
    descriptions = []
    for reminder in all_reminders_for_a_user:
        next_reminder_details = DynamoBackend.get_a_reminder_for_a_user(
            reminder.reminder_id, user
        )
        next_reminder_date_time = next_reminder_details[0].next_reminder_date_time
        next_reminder_date = datetime.datetime.strftime(
            next_reminder_date_time, "%d/%m/%y"
        )
        todays_date = datetime.datetime.strftime(datetime.datetime.now(), "%d/%m/%y")
        if todays_date == next_reminder_date:
            expiration_str = datetime.datetime.strftime(
                next_reminder_details[0].reminder_expiration_date_time,
                "%d %B, %Y %H:%M",
            )
            reminder_text = (
                f"{next_reminder_details[0].reminder_description} \n "
                f"Reminder due date: {expiration_str}"
            )
            descriptions.append(reminder_text)

    return descriptions


def get_user_email_from_pool(user, user_pool_id):
    """Get the user email."""
    session = boto3.session.Session()
    client = session.client("cognito-idp")
    response = client.admin_get_user(UserPoolId=user_pool_id, Username=user)
    for attributes in response["UserAttributes"]:
        if attributes["Name"] == "email":
            return attributes["Value"]


def send_reminder_message(message_arn, message):
    """Send a reminder email to the email address."""
    client = boto3.client("sns")
    return client.publish(TopicArn=message_arn, Message=message)


def filter_sns_arn_by_user(username):
    """Filter SNS ARNs for a specific user."""
    client = boto3.client("sns")
    try:
        # Call the list_topics API to get all SNS topics
        topics_data = client.list_topics()
        topics = topics_data["Topics"]

        subscribers = []

        relevant_topics = [
            topic for topic in topics if username.capitalize() in topic["TopicArn"]
        ]

        # Iterate through each topic
        for topic in relevant_topics:
            # Get ARN of the topic
            topic_arn = topic["TopicArn"]

            # Call the list_subscriptions_by_topic API to get subscribers for the topic
            subscriptions_data = client.list_subscriptions_by_topic(TopicArn=topic_arn)
            subscriptions = subscriptions_data["Subscriptions"]

            # Add subscribers for the topic to the result array
            subscribers.append({"topicArn": topic_arn, "subscriptions": subscriptions})
        logging.info(f"Details of subscriptions for {username} are:")
        logging.debug(subscribers)
        # Return the result containing subscribers for all topics
        return subscribers
    except Exception:
        raise ValueError(f"Could not filter through the subscriptions for {username}")


def query_and_send_reminders(event, context):
    """Query Dynamodb table and send reminders if has to be reminded today."""
    # At the moment the lambda function needs to have the users for whom
    # we need to check the reminders, this is done in the interest of cost
    # otherwise we have to do a scan on the table
    users = event.get("users")
    user_pool_id = event.get("user_pool_id")
    if users is None:
        raise ValueError(
            "The data for the lambda function needs to accept a list of users!"
        )
    reminders_for_which_we_need_to_remind = {"details": {}}
    for user in users:
        username = user["username"]
        # Get the details of the user email from cognito
        user_email = get_user_email_from_pool(username, user_pool_id)
        # Get the reminder description from the database
        descriptions = get_reminder_description_for_reminders_for_today(username)
        reminders_for_which_we_need_to_remind["details"][username] = {
            "email": user_email
        }
        # Send sns messages for all the users and for all the descriptions(which means
        # that there are multiple reminders for that day
        reminders_for_which_we_need_to_remind["details"][username]["notifications"] = []
        for message_description in descriptions:
            message_arn = user["message_arn"]
            reminders_for_which_we_need_to_remind["details"][username][
                "notifications"
            ].append(
                {
                    "sns_response": send_reminder_message(
                        message_arn, message_description
                    ),
                    "message_body": message_description,
                }
            )
    return reminders_for_which_we_need_to_remind


def delete_expired_reminders(event, context):
    """Delete expired reminders for specified users.

    Just like the previous function we need to have the users
    for whom we like to do the deletion.
    """
    users = event.get("users")
    if users is None:
        raise ValueError(
            "The data for the lambda function needs to accept a list of users!"
        )
    details = {}
    for user in users:
        username = user["username"]
        details[username] = {"deleted": [], "not_deleted": []}
        reminders_for_user = DynamoBackend.get_all_reminders_for_a_user(
            user_id=username
        )
        for reminder in reminders_for_user:
            parsed_reminder = data_structures.AllRemindersPerUser.parse_obj(
                reminder.attribute_values
            )
            if (
                parsed_reminder.reminder_expiration_date_time.date()
                < datetime.datetime.now().date()
            ):
                details[username]["deleted"].append(parsed_reminder.reminder_title)
                DynamoBackend.delete_a_reminder(reminder_id=parsed_reminder.reminder_id)
            else:
                details[username]["not_deleted"].append(
                    {
                        "reminder_id": parsed_reminder.reminder_id,
                        "reminder_title": parsed_reminder.reminder_title,
                    }
                )

    return details
