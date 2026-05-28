"""Tests for language-learning auth context extraction."""

import pytest
from fastapi import HTTPException, Request

from api.auth import get_user_context


def request_with_scope(scope: dict) -> Request:
    return Request({
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        **scope,
    })


def test_get_user_context_reads_cognito_claims(monkeypatch):
    """API Gateway authorizer claims are the production user source."""
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    request = request_with_scope({
        "aws.event": {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:username": "subhayan",
                        "email": "subhayan@example.com",
                    }
                }
            }
        }
    })

    user_context = get_user_context(request)

    assert user_context.user_name == "subhayan"
    assert user_context.user_email == "subhayan@example.com"


def test_get_user_context_raises_without_claims_outside_local(monkeypatch):
    """Production requests must arrive with API Gateway authorizer context."""
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    request = request_with_scope({})

    with pytest.raises(HTTPException) as exc_info:
        get_user_context(request)

    assert exc_info.value.status_code == 401


def test_get_user_context_allows_local_development(monkeypatch):
    """Local development keeps working without API Gateway."""
    monkeypatch.setenv("ENVIRONMENT", "local")
    request = request_with_scope({})

    user_context = get_user_context(request)

    assert user_context.user_name == "local_test_user"
