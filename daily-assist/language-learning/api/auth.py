"""Authentication dependency for the language learning API."""

import os
from dataclasses import dataclass

from fastapi import HTTPException, Request


@dataclass(frozen=True)
class UserDetails:
    user_name: str
    user_email: str


def get_user_context(request: Request) -> UserDetails:
    """
    Extract the authenticated Cognito user from an API Gateway Lambda event.

    The first migration step only enforces that a user is authenticated. The
    language-learning data model remains global until a later per-user schema
    migration adds ownership columns.
    """
    if "aws.event" in request.scope:
        event = request.scope["aws.event"]
        if "requestContext" in event and "authorizer" in event["requestContext"]:
            claims = event["requestContext"]["authorizer"]["claims"]
            return UserDetails(
                user_name=claims["cognito:username"],
                user_email=claims["email"],
            )

    if os.getenv("ENVIRONMENT") == "local":
        return UserDetails(
            user_name="local_test_user",
            user_email="test@example.com",
        )

    raise HTTPException(
        status_code=401,
        detail="Unauthorized - No user context found",
    )
