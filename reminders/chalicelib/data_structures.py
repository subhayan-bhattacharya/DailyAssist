import pydantic
from typing import Sequence, Optional
import datetime
from enum import Enum


def _datetime_validator(value: str) -> datetime.datetime:
    return datetime.datetime.strptime(value, "%d/%m/%y %H:%M")


class ReminderFrequency(Enum):
    once = ("once",)
    monthly = "monthly"
    daily = "daily"
    yearly = "yearly"


class UserDetails(pydantic.BaseModel):
    user_name: str
    user_email: str


class ReminderDetailsFromRequest(pydantic.BaseModel):
    reminder_title: str
    reminder_description: str
    reminder_tags: Sequence[str]
    reminder_frequency: ReminderFrequency
    should_expire: bool
    reminder_expiration_date_time: Optional[datetime.datetime]
    next_reminder_date_time: Optional[datetime.datetime]

    _validate_next_reminder_date_time = pydantic.validator(
        "next_reminder_date_time", pre=True, allow_reuse=True
    )(_datetime_validator)
    _validate_reminder_expiration_date_time = pydantic.validator(
        "reminder_expiration_date_time", pre=True, allow_reuse=True
    )(_datetime_validator)


class NewReminder(pydantic.BaseModel):
    reminder_id: str
    user_id: str
    reminder_title: str
    reminder_description: str
    reminder_tags: Sequence[str]
    reminder_frequency: str
    should_expire: bool
    reminder_expiration_date_time: Optional[datetime.datetime]
    next_reminder_date_time: datetime.datetime
    reminder_title_reminder_id: str
