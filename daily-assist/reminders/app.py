"""Main FastAPI application for daily assist reminders service."""

import json
import logging
import os
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Configure logging for Lambda (prints to CloudWatch)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

from core import data_structures
from core.lambda_handlers import (
    delete_expired_reminders,
    query_and_send_reminders,
)
from core.utils import (
    create_new_reminder,
    delete_reminder_for_user,
    get_all_reminders_for_user,
    get_all_tags_for_user,
    share_reminder_with_user,
    update_reminder_for_user,
    view_reminder_details_for_user,
)

app = FastAPI(title="Daily Assist Reminders API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://poulomi-subhayan.click",
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to extract user details from Lambda event context
# This mimics Chalice's CognitoUserPoolAuthorizer behavior
def get_user_context(request: Request) -> data_structures.UserDetails:
    """
    Extract user details from API Gateway Lambda event.

    When API Gateway uses Cognito authorizer, user info is available in:
    request.scope["aws.event"]["requestContext"]["authorizer"]["claims"]

    For local development without API Gateway, you can set a mock user.
    """
    # Check if running in Lambda with API Gateway
    if "aws.event" in request.scope:
        event = request.scope["aws.event"]
        if "requestContext" in event and "authorizer" in event["requestContext"]:
            claims = event["requestContext"]["authorizer"]["claims"]
            return data_structures.UserDetails(
                user_name=claims["cognito:username"],
                user_email=claims["email"]
            )

    # For local development, return mock user or raise error
    # You can customize this based on your local testing needs
    if os.getenv("ENVIRONMENT") == "local":
        return data_structures.UserDetails(
            user_name="local_test_user",
            user_email="test@example.com"
        )

    raise HTTPException(
        status_code=401,
        detail="Unauthorized - No user context found"
    )


UserContext = Annotated[data_structures.UserDetails, Depends(get_user_context)]


# Lambda function handlers (for scheduled tasks)
# These will be invoked directly by Lambda, not through API Gateway
def lambda_query_and_send_reminders_handler(event, context):
    """Lambda function to query and send reminders."""
    return query_and_send_reminders(event, context)


def lambda_delete_expired_reminders_handler(event, context):
    """Lambda function to delete expired reminders."""
    return delete_expired_reminders(event, context)


# API Routes

@app.post(
    "/reminders/{reminder_id}/share",
    response_model=data_structures.MessageResponse,
    tags=["Reminders"]
)
def share_a_reminder_with_someone(
    reminder_id: str,
    share_request: data_structures.ShareReminderRequest,
    user_context: UserContext
):
    """Try to share a reminder with someone."""
    return share_reminder_with_user(reminder_id, share_request, user_context)


@app.post(
    "/reminders",
    response_model=data_structures.CreateReminderResponse,
    status_code=201,
    tags=["Reminders"]
)
def create_a_new_reminder(
    create_request: data_structures.CreateReminderRequest,
    user_context: UserContext
):
    """Creates a new reminder in the database."""
    return create_new_reminder(create_request, user_context)


@app.get(
    "/tags",
    response_model=list[str],
    tags=["Tags"]
)
def get_all_tags_for_a_user(user_context: UserContext):
    """Gets the list of all reminder tags currenty in the database."""
    return get_all_tags_for_user(user_context)


@app.get(
    "/reminders",
    response_model=list[data_structures.AllRemindersPerUser],
    tags=["Reminders"]
)
def get_all_reminders_for_a_user(
    user_context: UserContext,
    tag: Optional[str] = Query(None, description="Filter reminders by tag")
):
    """Gets the list of all reminders for a user."""
    return get_all_reminders_for_user(user_context, tag)


@app.get(
    "/reminders/{reminder_id}",
    response_model=data_structures.SingleReminder,
    tags=["Reminders"]
)
def view_details_of_a_reminder_for_a_user(
    reminder_id: str,
    user_context: UserContext
):
    """View the details of a reminder for the user making the request."""
    return view_reminder_details_for_user(reminder_id, user_context)


@app.delete(
    "/reminders/{reminder_id}",
    response_model=data_structures.ReminderIdResponse,
    tags=["Reminders"]
)
def delete_a_reminder(
    reminder_id: str,
    user_context: UserContext
):
    """Delete a reminder."""
    return delete_reminder_for_user(reminder_id, user_context)


@app.put(
    "/reminders/{reminder_id}",
    response_model=data_structures.ReminderIdResponse,
    tags=["Reminders"]
)
def update_a_reminder(
    reminder_id: str,
    update_request: data_structures.UpdateReminderRequest,
    user_context: UserContext
):
    """Update a reminder with the given reminder id."""
    return update_reminder_for_user(reminder_id, update_request, user_context)


# Mangum handler for AWS Lambda
_mangum_handler = Mangum(app)


def handler(event, context):
    """Lambda handler with logging."""
    logger.info("=== Lambda invoked ===")
    logger.info(f"HTTP Method: {event.get('httpMethod', 'N/A')}")
    logger.info(f"Path: {event.get('path', 'N/A')}")
    logger.info(f"Headers: {json.dumps(event.get('headers', {}))}")
    logger.info(f"Request Context: {json.dumps(event.get('requestContext', {}), default=str)}")

    try:
        response = _mangum_handler(event, context)
        logger.info(f"Response status: {response.get('statusCode', 'N/A')}")
        return response
    except Exception as e:
        logger.error(f"Lambda error: {str(e)}", exc_info=True)
        raise
