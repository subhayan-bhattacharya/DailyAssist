import datetime
import itertools
import json
import logging
import os
import traceback
import uuid

import boto3
from chalice import Chalice, CognitoUserPoolAuthorizer, Response
from pydantic import ValidationError

from chalicelib import data_structures
from chalicelib.backend.dynamodb.dynamo_backend import DynamoBackend

app = Chalice(app_name="daily_assist_reminders")


authorizer = CognitoUserPoolAuthorizer(
    os.getenv("COGNITO_USER_POOL_NAME"),
    provider_arns=[os.getenv("COGNITO_USER_POOL_ARN")],
)


def get_reminder_description_for_reminders_for_today(user):
    # Get the reminder description from the database
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
            descriptions.append(
                f"{next_reminder_details[0].reminder_description} \n Reminder due date: "
                f"{datetime.datetime.strftime(next_reminder_details[0].reminder_expiration_date_time, '%d %B, %Y %H:%M')}"
            )

    return descriptions


def get_user_email_from_pool(user, user_pool_id):
    """Get the user email."""
    session = boto3.session.Session()
    client = session.client("cognito-idp")
    response = client.admin_get_user(UserPoolId=user_pool_id, Username=user)
    for attributes in response["UserAttributes"]:
        if attributes["Name"] == "email":
            return attributes["Value"]


def _send_reminder_message(message_arn, message):
    """Send a reminder email to the email address."""
    client = boto3.client("sns")
    return client.publish(TopicArn=message_arn, Message=message)


def filter_sns_arn_by_user(username):
    """This function goes through all the resource ARN for SNS and filters for the user."""
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
        print(f"Details of subscriptions for {username} are:")
        print(subscribers)
        # Return the result containing subscribers for all topics
        return subscribers
    except Exception as e:
        raise ValueError(f"Could not filter through the subscriptions for {username}")


@app.lambda_function(name="queryAndSendReminders")
def query_and_send_reminders(event, context):
    """Query Dynamodb table and send reminders if has to be reminded today."""
    # At the moment the lambda function needs to have the users for whom
    # we need to check the reminders, this is done in the interest of cost
    # otherwise we have to do a scan on the table
    users = event.get("users")
    user_pool_id = event.get("user_pool_id")
    if users is None:
        raise ValueError(
            f"The data for the lambda function needs to accept a list of users!"
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
                    "sns_response": _send_reminder_message(
                        message_arn, message_description
                    ),
                    "message_body": message_description,
                }
            )
    return reminders_for_which_we_need_to_remind


@app.lambda_function(name="deleteExpiredReminders")
def delete_expired_reminders(event, context):
    """
    Deletes expired reminders.
    Just like the previous function we need to have the users
    for whom we like to do the deletion.
    """
    users = event.get("users")
    if users is None:
        raise ValueError(
            f"The data for the lambda function needs to accept a list of users!"
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

        if reminder_details.user_name is None:
            # this basically means that the user is creating a new reminder
            user_details = data_structures.UserDetails(
                user_name=request_context["authorizer"]["claims"]["cognito:username"],
                user_email=request_context["authorizer"]["claims"]["email"],
            )
            username = user_details.user_name
        else:
            # in this case this means that a previously created reminder is being shared
            # with someone else
            # this should entail creating a new reminder with same reminder details but different user name
            username = reminder_details.user_name
        # Check if the user has already created a similar entry by querying the GSI
        reminders_present = list(
            DynamoBackend.get_a_reminder_gsi(username, reminder_details.reminder_title)
        )
        if len(reminders_present) > 0:
            logging.error(f"There are reminders present {reminders_present}")
            raise ValueError(
                f"There is already a reminder with name {reminder_details.reminder_title}"
                f" for user {username}"
            )

        if reminder_details.reminder_id is None:
            reminder_id = str(uuid.uuid1())
        else:
            # Case when this happens is when a reminder is shared with someone
            reminder_id = reminder_details.reminder_id

        reminder_details_as_dict = reminder_details.dict()
        reminder_details_as_dict["reminder_frequency"] = reminder_details_as_dict[
            "reminder_frequency"
        ].value

        # in the case when a reminder is shared with someone
        # the reminder_details_as_dict would contain the value of
        # username and reminder_id.
        new_reminder = data_structures.SingleReminder.parse_obj(
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
        # We also want to send a confirmation message to the user
        # when the reminder is created.
        user_subscriptions = filter_sns_arn_by_user(username)
        user_readable_expiration_date = (
            reminder_details.reminder_expiration_date_time.strftime("%d/%m/%y %H:%M")
        )
        message = f"New reminder added for date : {user_readable_expiration_date}.Reminder Details : {reminder_details.reminder_description}"
        for subscriber in user_subscriptions:
            _send_reminder_message(subscriber["topicArn"], message)

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
    "/tags",
    methods=["GET"],
    authorizer=authorizer,
)
def get_all_tags_for_a_user():
    """Gets the list of all reminder tags currenty in the database."""
    try:
        request_context = app.current_request.context
        user_details = data_structures.UserDetails(
            user_name=request_context["authorizer"]["claims"]["cognito:username"],
            user_email=request_context["authorizer"]["claims"]["email"],
        )
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
        tag_name = app.current_request.query_params.get('tag')
        print(f"Tag name provided is {tag_name}")
        if tag_name is not None:
            all_reminder_details = DynamoBackend.get_all_reminders_for_a_user_by_tag(
                user_id=user_details.user_name,
                tag=tag_name
            )
        else:
            print("No tag provided... getting all reminders for the user...")
            all_reminder_details = DynamoBackend.get_all_reminders_for_a_user(
                user_id=user_details.user_name
            )
        all_reminders_per_user = [
            data_structures.AllRemindersPerUser.parse_obj(reminder.attribute_values)
            for reminder in all_reminder_details
        ]
        sorted_reminders_per_user = sorted(
            all_reminders_per_user, key=lambda x: x.reminder_expiration_date_time
        )

        return [json.loads(reminder.json()) for reminder in sorted_reminders_per_user]
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
        user_details = data_structures.UserDetails(
            user_name=request_context["authorizer"]["claims"]["cognito:username"],
            user_email=request_context["authorizer"]["claims"]["email"],
        )
        single_reminder_details = DynamoBackend.get_a_reminder_for_a_user(
            reminder_id=reminder_id, user_name=user_details.user_name
        )
        if len(single_reminder_details) == 0:
            raise ValueError(f"No such reminder with id: {reminder_id}")
        return json.loads(
            data_structures.SingleReminder.parse_obj(
                single_reminder_details[0].attribute_values
            ).json()
        )
    except ValidationError as error:
        traceback.print_exc()
        # This is a hack to get the error message string in pydantic
        error_message = str(error.raw_errors[0].exc)
        return Response(
            body=json.dumps(
                {
                    "message": f"Could not retrieve reminder with reminder id {reminder_id}!!",
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
                    "message": f"Could not retrieve reminder with reminder id {reminder_id}!!",
                    "error": str(error),
                },
            ),
            status_code=400,
            headers={"Content-Type": "application/json"},
        )


@app.route("/reminders/{reminder_id}", methods=["PUT"], authorizer=authorizer)
def update_a_reminder(reminder_id: str):
    """update a reminder with the given reminder id."""
    try:
        request_body = json.loads(app.current_request.raw_body.decode())
        request_body["reminder_frequency"] = data_structures.ReminderFrequency[
            request_body["reminder_frequency"]
        ]
        reminder_details = data_structures.ReminderDetailsFromRequest.parse_obj(
            request_body
        )
        reminder_details_as_dict = reminder_details.dict()
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
        body=json.dumps({"message": "Reminder successfully updated!"}),
        status_code=200,
        headers={"Content-Type": "application/json"},
    )
