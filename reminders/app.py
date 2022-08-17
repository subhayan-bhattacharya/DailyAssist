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


def get_reminder_description_for_reminders_for_today(user):
    # Get the reminder description from the database
    all_reminders_for_a_user = DynamoBackend.get_all_reminders_for_a_user(
        user_id=user
    )
    descriptions = []
    for reminder in all_reminders_for_a_user:
        next_reminder_details = DynamoBackend.get_a_reminder_for_a_user(
            reminder.reminder_id, user
        )
        next_reminder_date_time = next_reminder_details[0].next_reminder_date_time
        next_reminder_date = datetime.datetime.strftime(
            next_reminder_date_time, "%d/%m/%y"
        )
        todays_date = datetime.datetime.strftime(
            datetime.datetime.now(), "%d/%m/%y"
        )
        if todays_date == next_reminder_date:
                descriptions.append(next_reminder_details.reminder_description)
    return descriptions


def get_user_email_from_pool(user, user_pool_id):
    """Get the user email."""


# This lambda function is temporary , it will be removed when we have the
# mobile application in place.
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
        # Get the details of the user email from cognito
        user_email = get_user_email_from_pool(user, user_pool_id)
        # Get the reminder description from the database
        descriptions = get_reminder_description_for_reminders_for_today(user)
        reminders_for_which_we_need_to_remind["details"][user] = {
            "email": user_email,
            "descriptions": descriptions
        }
    return reminders_for_which_we_need_to_remind


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
        all_reminder_details = DynamoBackend.get_all_reminders_for_a_user(
            user_id=user_details.user_name
        )
        return [
            json.loads(
                data_structures.AllRemindersPerUser.parse_obj(
                    reminder.attribute_values
                ).json()
            )
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
