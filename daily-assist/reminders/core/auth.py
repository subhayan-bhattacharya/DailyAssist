"""Authentication helpers for FastAPI request handlers."""

import os

from fastapi import HTTPException, Request

from core import data_structures


def get_user_context(request: Request) -> data_structures.UserDetails:
    """
    Extract the authenticated Cognito user from an API Gateway Lambda event.

    API Gateway's Cognito authorizer injects claims into the Lambda event that
    Mangum exposes through the ASGI request scope.
    """
    if "aws.event" in request.scope:
        event = request.scope["aws.event"]
        if "requestContext" in event and "authorizer" in event["requestContext"]:
            claims = event["requestContext"]["authorizer"]["claims"]
            return data_structures.UserDetails(
                user_name=claims["cognito:username"],
                user_email=claims["email"],
            )

    if os.getenv("ENVIRONMENT") == "local":
        return data_structures.UserDetails(
            user_name="local_test_user",
            user_email="test@example.com",
        )

    raise HTTPException(
        status_code=401,
        detail="Unauthorized - No user context found",
    )
