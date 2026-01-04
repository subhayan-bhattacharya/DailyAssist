# Script to create the database in dynamodb local database
# or inside aws account linked to the profile
#
# Usage:
#   For local DynamoDB:
#     ENVIRONMENT=local python table_create_update.py
#
#   For AWS DynamoDB:
#     python table_create_update.py

import os
from pprint import pprint

import boto3


def create_reminders_table(profile: str = None, endpoint_url: str = None):
    """Create the reminders table.

    Args:
        profile: AWS profile name to use (optional)
        endpoint_url: DynamoDB endpoint URL (for local testing)

    Returns:
        Response from create_table operation
    """
    # Create session with profile if provided
    if profile:
        session = boto3.session.Session(profile_name=profile)
        dynamodb = session.resource("dynamodb", endpoint_url=endpoint_url)
    else:
        # Use default credentials/profile
        dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint_url)

    response = dynamodb.create_table(
        TableName="Reminders",
        KeySchema=[
            {"AttributeName": "reminder_id", "KeyType": "HASH"},
            {"AttributeName": "user_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "reminder_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "reminder_title", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "UserIdReminderTitleGsi2",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "reminder_title", "KeyType": "RANGE"},
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": [
                        "reminder_expiration_date_time",
                        "reminder_id",
                        "reminder_tags",
                    ],
                },
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return response


if __name__ == "__main__":
    # Check if using local DynamoDB via ENVIRONMENT variable
    environment = os.getenv("ENVIRONMENT", "")

    if environment == "local":
        # Use local DynamoDB
        endpoint_url = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8000")
        profile = os.getenv("AWS_PROFILE", "local-dynamodb")

        print(f"Creating table in LOCAL DynamoDB")
        print(f"  Endpoint: {endpoint_url}")
        print(f"  Profile: {profile}")

        response = create_reminders_table(profile=profile, endpoint_url=endpoint_url)
    else:
        # Use AWS DynamoDB
        profile = os.getenv("AWS_PROFILE", "daily_assist")

        print(f"Creating table in AWS DynamoDB")
        print(f"  Profile: {profile}")

        response = create_reminders_table(profile=profile)

    print("\nTable creation response:")
    pprint(response, depth=4)
