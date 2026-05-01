"""Entry point for scheduled Lambda functions.

This module is the handler entry point for the scheduled Lambda functions
(EventBridge rules). It intentionally does not import app.py to avoid
pulling in FastAPI and other API-only dependencies.
"""

from core.lambda_handlers import delete_expired_reminders, query_and_send_reminders


def lambda_query_and_send_reminders_handler(event, context):
    """Lambda handler to query DynamoDB and send due reminders via SNS."""
    return query_and_send_reminders(event, context)


def lambda_delete_expired_reminders_handler(event, context):
    """Lambda handler to delete expired reminders from DynamoDB."""
    return delete_expired_reminders(event, context)
