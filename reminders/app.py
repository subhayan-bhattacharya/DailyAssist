"""Main Chalice application for daily assist reminders service."""

import os

from chalice import Chalice, CognitoUserPoolAuthorizer
from chalicelib.lambda_handlers import (
    delete_expired_reminders,
    query_and_send_reminders,
)
from chalicelib.utils import (
    create_new_reminder,
    delete_reminder_for_user,
    get_all_reminders_for_user,
    get_all_tags_for_user,
    share_reminder_with_user,
    update_reminder_for_user,
    view_reminder_details_for_user,
)

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
    return get_all_reminders_for_user(app.current_request, app.current_request.context)


@app.route("/reminders/{reminder_id}", methods=["GET"], authorizer=authorizer)
def view_details_of_a_reminder_for_a_user(reminder_id: str):
    """View the details of a reminder for the user making the request."""
    return view_reminder_details_for_user(reminder_id, app.current_request.context)


@app.route("/reminders/{reminder_id}", methods=["DELETE"], authorizer=authorizer)
def delete_a_reminder(reminder_id: str):
    """Delete a reminder."""
    return delete_reminder_for_user(reminder_id, app.current_request.context)


@app.route("/reminders/{reminder_id}", methods=["PUT"], authorizer=authorizer)
def update_a_reminder(reminder_id: str):
    """Update a reminder with the given reminder id."""
    return update_reminder_for_user(
        reminder_id, app.current_request, app.current_request.context
    )
