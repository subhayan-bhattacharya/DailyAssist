# Sample script to create the database in dynamodb local database
# or inside aws account linked to the profile

from pprint import pprint

import boto3


def create_reminders_table(profile: str, endpoint: str = "local"):
    """Just create the reminders table."""
    session = boto3.session.Session(profile_name=profile)

    if endpoint == "local":
        dynamodb = session.resource("dynamodb", endpoint_url="http://localhost:8000")
    elif endpoint == "aws":
        dynamodb = session.resource("dynamodb")

    response = dynamodb.create_table(
        TableName="Reminders",
        KeySchema=[
            {"AttributeName": "reminder_id", "KeyType": "HASH"},
            {"AttributeName": "user_id", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "reminder_id", "AttributeType": "S"},
            {"AttributeName": "user_id", "AttributeType": "S"},
            {"AttributeName": "reminder_title_reminder_id", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "UserTitleReminderIdGsi",
                "KeySchema": [
                    {"AttributeName": "user_id", "KeyType": "HASH"},
                    {"AttributeName": "reminder_title_reminder_id", "KeyType": "RANGE"},
                ],
                "Projection": {
                    "ProjectionType": "INCLUDE",
                    "NonKeyAttributes": [
                        "reminder_expiration_date_time",
                        "reminder_id",
                    ],
                },
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    return response


if __name__ == "__main__":
    response = create_reminders_table(profile="daily_assist", endpoint="aws")
    # response = create_reminders_table(profile='dynamodb_local')
    pprint(response, depth=4)
