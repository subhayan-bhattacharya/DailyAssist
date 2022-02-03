"""Module having the models for pynamodb."""

from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute, UTCDateTimeAttribute, UnicodeSetAttribute
)


class Reminders(Model):
    """Model class for the Reminders table."""

    # Information on global secondary index for the table
    # user_id (hash key) + reminder_id+reminder_title(sort key)
    class Meta:
        table_name = 'Reminders'

    reminder_id = UnicodeAttribute(hash_key=True)
    user_id = UnicodeAttribute(range_key=True)
    reminder_title = UnicodeAttribute()
    reminder_title_reminder_id = UnicodeAttribute()
    reminder_tags = UnicodeSetAttribute()
    reminder_expiration_date_time = UTCDateTimeAttribute()
    reminder_frequency = UnicodeAttribute(default='Only once')
    next_reminder_date_time = UTCDateTimeAttribute()
    reminder_description = UnicodeAttribute()
