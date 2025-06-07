import datetime
from enum import Enum
from typing import Optional, Sequence

import pydantic
import pytz
from dateutil.relativedelta import relativedelta
from pytz import timezone


def get_localized_date(date: datetime.datetime):
    if date.tzinfo is not None and date.tzinfo.utcoffset(date) is not None:
        print(f"This date {date } is tz aware...")
        return date

    print(f"This date {date} does not seem to be tz aware..")
    utc = pytz.utc
    localized_time = utc.localize(date)
    print(f"Time after localization : {localized_time}")
    return localized_time


class ReminderFrequency(Enum):
    """Reminder frequency enumeration."""

    once = "once"
    monthly = "monthly"
    daily = "daily"
    yearly = "yearly"


class AllRemindersPerUser(pydantic.BaseModel):
    """Base model for the response of get all reminders."""

    user_id: str
    reminder_title: str
    reminder_id: str
    reminder_expiration_date_time: Optional[datetime.datetime]

    model_config = {
        "json_encoders": {
            datetime.datetime: lambda v: v.strftime("%d %B %Y, %I:%M %p").replace(
                " 0", " "
            ),
        }
    }


class UserDetails(pydantic.BaseModel):
    """Base model for user making the request."""

    user_name: str
    user_email: str


def _calculate_next_reminder_date(
    reminder_frequency: ReminderFrequency,
    reminder_expiration_date_time: Optional[datetime.datetime],
) -> datetime.datetime:
    """Calculate next reminder from frequency and expiration date."""
    calculated_next_reminder = None
    current_date_time = datetime.datetime.now()
    if reminder_frequency == ReminderFrequency["once"]:
        if reminder_expiration_date_time is None:
            # you need to set an expiration date also for this to work
            raise ValueError(
                f"If you select a reminder frequency of {reminder_frequency.value}"
                f" then a reminder expiration date is required"
            )
        else:
            # if the expiration date is not None
            # then the next reminder should be 1 day before the expiration data
            # since the frequency is just once
            calculated_next_reminder = (
                reminder_expiration_date_time + datetime.timedelta(days=-1)
            )
            if current_date_time > calculated_next_reminder:
                # we cannot set the next reminder to be in the past
                raise ValueError(
                    f"With a reminder frequency of {reminder_frequency.value}"
                    f" it is not possible to set the next reminder to 1 day before expiry!!"
                )
            return calculated_next_reminder

    if reminder_frequency == ReminderFrequency["monthly"]:
        # set the next reminder date to be 1 month from now
        calculated_next_reminder = current_date_time + relativedelta(months=1)
        # if the expiration date is given validate that it is not before the calculated
        # next reminder date
        if (
            reminder_expiration_date_time is not None
            and reminder_expiration_date_time < calculated_next_reminder
        ):
            raise ValueError(
                f"With a reminder frequency of {reminder_frequency.value}"
                f" it is not possible to set the next reminder to 1 month before expiry!!"
            )

    if reminder_frequency == ReminderFrequency["yearly"]:
        # set the next reminder date to be 1 year from now
        calculated_next_reminder = current_date_time + relativedelta(years=1)
        # if the expiration date is given validate that it is not before the calculated
        # next reminder date
        if (
            reminder_expiration_date_time is not None
            and reminder_expiration_date_time < calculated_next_reminder
        ):
            raise ValueError(
                f"With a reminder frequency of {reminder_frequency.value}"
                f" it is not possible to set the next reminder to 1 year before expiry!!"
            )

    if reminder_frequency == ReminderFrequency["daily"]:
        # set the next reminder date to be a day from now
        calculated_next_reminder = current_date_time + relativedelta(days=1)
        # if the expiration date is given validate that it is not before the calculated
        # next reminder date
        if (
            reminder_expiration_date_time is not None
            and reminder_expiration_date_time < calculated_next_reminder
        ):
            raise ValueError(
                f"With a reminder frequency of {reminder_frequency.value}"
                f" it is not possible to set the next reminder to 1 day before expiry!!"
            )

    assert calculated_next_reminder is not None
    return calculated_next_reminder


class ReminderDetailsFromRequest(pydantic.BaseModel):
    reminder_title: str
    reminder_description: str
    reminder_tags: Sequence[str]
    reminder_frequency: ReminderFrequency
    should_expire: bool
    reminder_expiration_date_time: Optional[datetime.datetime] = None
    next_reminder_date_time: Optional[datetime.datetime] = None
    # The below 2 attributes are going to be sent in the request
    # in the case when a reminder needs to be shared with someone
    user_name: Optional[str] = None
    reminder_id: Optional[str] = None

    @pydantic.field_validator("reminder_title")
    def validate_title(cls, value: str) -> str:
        """Validate that the title is not empty or whitespace only."""
        if not value or value.strip() == "":
            raise ValueError("Title cannot be empty or whitespace only")
        return value

    @pydantic.field_validator("reminder_tags", mode="before")
    def convert_to_list_if_set(cls, value):
        """Convert set to list if needed."""
        if isinstance(value, set):
            return list(value)
        return value

    @pydantic.field_validator("next_reminder_date_time", mode="before")
    def _datetime_validator_next_reminder_date_time(
        cls, value: str | datetime.datetime
    ) -> datetime.datetime:
        """Validate and convert next reminder datetime."""
        print(
            f"The value of next_reminder_date_time in the pre validator is {value} and its type is {type(value)}"
        )
        # This is usually the case when we are updating the reminder
        # Has to be changed to better code when we have a frontend for this
        if not isinstance(value, datetime.datetime):
            try:
                print(f"Trying to parse date with format : %d/%m/%y %H:%M")
                next_reminder_date_time = datetime.datetime.strptime(
                    value, "%d/%m/%y %H:%M"
                )
            except ValueError as error:
                print(
                    f"Parsing of next reminder date encountered error : {error}...trying with format %d %B %Y, %I:%M %p"
                )
                next_reminder_date_time = datetime.datetime.strptime(
                    value, "%d %B %Y, %I:%M %p"
                )
        else:
            next_reminder_date_time = value
        print(f"Formatting or no formatting the value is : {next_reminder_date_time}")
        if next_reminder_date_time < datetime.datetime.now():
            raise ValueError(
                "The next reminder date and time should be in the future !!"
            )
        return next_reminder_date_time

    @pydantic.field_validator("reminder_expiration_date_time", mode="before")
    def _datetime_validator_reminder_expiration_date_time(
        cls, value: str | datetime.datetime | None
    ) -> datetime.datetime | None:
        """Validate and convert expiration datetime."""
        if value is None:
            return None
            
        print(
            f"The value of reminder_expiration_date_time in the pre validator is {value} and its type is {type(value)}"
        )
        if isinstance(value, datetime.datetime):
            # This case is when for example we are updating an existing reminder
            # but we do not want to change the existing reminder expiration date.
            return value
        try:
            print(f"Trying to parse date with format : %d/%m/%y %H:%M")
            reminder_expiration_date_time = datetime.datetime.strptime(
                value, "%d/%m/%y %H:%M"
            )
        except ValueError as error:
            print(
                f"Parsing of reminder expiration date encountered error : {error}...trying with format %d %B %Y, %I:%M %p"
            )
            reminder_expiration_date_time = datetime.datetime.strptime(
                value, "%d %B %Y, %I:%M %p"
            )
        print(
            f"Formatting or no formatting the value is : {reminder_expiration_date_time}"
        )
        if reminder_expiration_date_time < datetime.datetime.now():
            raise ValueError(
                "The reminder expiration date and time should be in the future !!"
            )
        return reminder_expiration_date_time

    @pydantic.model_validator(mode="after")
    def expiration_and_next_reminder_date_validator(self) -> "ReminderDetailsFromRequest":
        """Validate expiration and next reminder dates."""
        print(f"Inside the model validator")
        if not self.should_expire:
            print(
                f"Since the reminder should never expire i will pop the expiration date and time which has value : {self.reminder_expiration_date_time}"
            )
            # Remove the attribute entirely instead of setting to None
            delattr(self, "reminder_expiration_date_time")
            # If the reminder should never expire then we do not need reminder expiration date and time
            # for the next reminder we can calculate it
            if self.next_reminder_date_time is None:
                print(
                    f"There is no value for next reminder date... we need to calculate"
                )
                # if the next reminder date is not given we have to calculate it
                calculated_next_reminder_date_and_time = _calculate_next_reminder_date(
                    self.reminder_frequency, None
                )
                self.next_reminder_date_time = calculated_next_reminder_date_and_time
                print(
                    f"The calculated value for next reminder date is {calculated_next_reminder_date_and_time}"
                )
        else:
            print("This reminder should expire..")
            if not self.reminder_expiration_date_time:
                raise ValueError(
                    f"Since the reminder should expire...an expiration date should be given"
                )
            if self.next_reminder_date_time is None:
                # if the next reminder date is not given we have to calculate it
                calculated_next_reminder_date_and_time = _calculate_next_reminder_date(
                    self.reminder_frequency, self.reminder_expiration_date_time
                )
                self.next_reminder_date_time = calculated_next_reminder_date_and_time
                print(
                    f"The calculated value of next reminder date is : {calculated_next_reminder_date_and_time}"
                )
            else:
                print("Trying to localize the next reminder time...")
                localized_next_reminder_date = get_localized_date(self.next_reminder_date_time)
                if self.reminder_expiration_date_time is not None:
                    print("Trying to localize the expiration date and time...")
                    localized_expiration_date = get_localized_date(
                        self.reminder_expiration_date_time
                    )
                    if localized_expiration_date < localized_next_reminder_date:
                        raise ValueError(
                            "The next reminder date and time cannot be later than the reminder expiration date!"
                        )
        return self


class SingleReminder(pydantic.BaseModel):
    """Model for a new reminder."""

    reminder_id: str
    user_id: str
    reminder_title: str
    reminder_description: str
    reminder_tags: Sequence[str]
    reminder_frequency: str
    should_expire: bool
    reminder_expiration_date_time: Optional[datetime.datetime]
    next_reminder_date_time: datetime.datetime
    reminder_creation_time: datetime.datetime

    model_config = {
        "json_encoders": {
            datetime.datetime: lambda v: v.strftime("%d %B %Y, %I:%M %p").replace(
                " 0", " "
            ),
        }
    }

    @pydantic.field_validator("reminder_tags", mode="before")
    def convert_to_list_if_set(cls, value):
        """Convert set to list if needed."""
        if isinstance(value, set):
            return list(value)
        return value
