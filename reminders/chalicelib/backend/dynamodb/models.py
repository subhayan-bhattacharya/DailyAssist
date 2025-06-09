"""Module having the models for pynamodb."""

from pynamodb.attributes import (
    BooleanAttribute,
    UnicodeAttribute,
    UnicodeSetAttribute,
    UTCDateTimeAttribute,
)
from pynamodb.indexes import GlobalSecondaryIndex, IncludeProjection
from pynamodb.models import Model


class UserIdReminderTitleIndex(GlobalSecondaryIndex):
    """Global secondary index for table Reminders.

    This index allows efficient querying of reminders by user_id and reminder_title.
    It includes additional attributes in its projection for common query needs.
    """

    class Meta:
        """Configuration for the GSI.

        Attributes:
            index_name: Name of the global secondary index.
            projection: Specifies which attributes are copied to the index.
        """

        index_name = "UserIdReminderTitleGsi2"
        projection = IncludeProjection(
            ["reminder_expiration_date_time", "reminder_id", "reminder_tags"]
        )

    # Global secondary index hash and range keys
    user_id = UnicodeAttribute(hash_key=True)
    reminder_title = UnicodeAttribute(range_key=True)


class Reminders(Model):
    """Model class for the Reminders table.

    This model represents a reminder in the DynamoDB table. Each reminder has
    a unique ID and is associated with a user. Reminders can be shared between
    users, which creates multiple entries with the same reminder_id but different
    user_ids.
    """

    class Meta:
        """Configuration for the Reminders table.

        Attributes:
            table_name: Name of the DynamoDB table.
            region: AWS region where the table is located.
        """

        table_name = "Reminders"
        region = "eu-central-1"

    # Primary key attributes
    reminder_id = UnicodeAttribute(hash_key=True)
    user_id = UnicodeAttribute(range_key=True)

    # Reminder details
    reminder_title = UnicodeAttribute()
    reminder_tags = UnicodeSetAttribute()
    reminder_description = UnicodeAttribute()
    reminder_frequency = UnicodeAttribute(default="once")
    reminder_expiration_date_time = UTCDateTimeAttribute(null=True)
    next_reminder_date_time = UTCDateTimeAttribute(null=True)
    reminder_creation_time = UTCDateTimeAttribute()
    should_expire = BooleanAttribute()

    # Global Secondary Index
    view_index = UserIdReminderTitleIndex()
