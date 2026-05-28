"""Tests for Reminders auth context extraction."""

import pytest
from fastapi import HTTPException, Request

from app import _redact_headers
from core.auth import get_user_context


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
                        "cognito:username": "poulomi",
                        "email": "poulomi@example.com",
                    }
                }
            }
        }
    })

    user_context = get_user_context(request)

    assert user_context.user_name == "poulomi"
    assert user_context.user_email == "poulomi@example.com"


def test_get_user_context_raises_without_claims_outside_local(monkeypatch):
    """Production requests must arrive with API Gateway authorizer context."""
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    request = request_with_scope({})

    with pytest.raises(HTTPException) as exc_info:
        get_user_context(request)

    assert exc_info.value.status_code == 401


def test_redact_headers_removes_authorization_token():
    """Lambda logs must not include bearer tokens."""
    headers = {
        "Authorization": "eyJraWQiOiJsecret",
        "Content-Type": "application/json",
    }

    redacted_headers = _redact_headers(headers)

    assert redacted_headers["Authorization"] == "[REDACTED]"
    assert redacted_headers["Content-Type"] == "application/json"
