"""Data structures for the reminders application."""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass, field
from typing import Optional, Sequence
from zoneinfo import ZoneInfo

from core.datetime_utils import DEFAULT_DATE_FORMATS, DateTimeUTC, parse_datetime
from core.reminder_frequency import (
    ReminderFrequency,
    calculate_next_reminder_date,
)
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class DateTimeConfig:
    """Configuration for datetime handling."""

    timezone: ZoneInfo = ZoneInfo("UTC")
    date_formats: list[str] = field(default_factory=lambda: DEFAULT_DATE_FORMATS.copy())


def format_datetime(dt: datetime.datetime) -> str:
    """Format a datetime object to string.

    Args:
        dt: The datetime to format

    Returns:
        A formatted datetime string
    """
    return dt.strftime("%d %B %Y, %I:%M %p").replace(" 0", " ")


class ReminderBase(BaseModel):
    """Base class for reminder models with common fields."""

    reminder_title: str
    reminder_description: str
    reminder_tags: Sequence[str]
    reminder_frequency: ReminderFrequency
    should_expire: bool
    reminder_expiration_date_time: Optional[DateTimeUTC] = None
    next_reminder_date_time: Optional[DateTimeUTC] = None

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime.datetime: format_datetime}
    )

    @field_validator("reminder_title")
    def validate_title(cls, value: str) -> str:
        """Validate that the title is not empty or whitespace only."""
        if not value or not value.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return value.strip()

    @field_validator("reminder_tags", mode="before")
    def convert_to_list_if_set(cls, value):
        """Convert set to list if needed."""
        return list(value) if isinstance(value, set) else value

    @field_validator(
        "next_reminder_date_time", "reminder_expiration_date_time", mode="before"
    )
    def parse_datetime_str(
        cls, value: str | datetime.datetime | None
    ) -> DateTimeUTC | None:
        """Parse datetime strings to UTC datetime objects."""
        try:
            return parse_datetime(value) if value is not None else None
        except ValueError as e:
            logger.error(f"Failed to parse datetime: {e}")
            raise


class ReminderDetailsFromRequest(ReminderBase):
    """Model for reminder details from incoming requests."""

    user_name: Optional[str] = None
    reminder_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_dates(self) -> ReminderDetailsFromRequest:
        """Validate expiration and next reminder dates."""
        try:
            if not self.should_expire:
                logger.debug("Reminder should not expire, removing expiration date")
                delattr(self, "reminder_expiration_date_time")

                if self.next_reminder_date_time is None:
                    logger.debug(
                        "Calculating next reminder date for non-expiring reminder"
                    )
                    self.next_reminder_date_time = calculate_next_reminder_date(
                        self.reminder_frequency
                    )
            else:
                if not self.reminder_expiration_date_time:
                    raise ValueError(
                        "Expiration date required when should_expire is True"
                    )

                if self.next_reminder_date_time is None:
                    logger.debug("Calculating next reminder date for expiring reminder")
                    self.next_reminder_date_time = calculate_next_reminder_date(
                        self.reminder_frequency, self.reminder_expiration_date_time
                    )
                elif self.next_reminder_date_time > self.reminder_expiration_date_time:
                    raise ValueError(
                        "Next reminder date cannot be later than expiration date"
                    )

            return self
        except Exception as e:
            logger.error(f"Failed to validate dates: {e}")
            raise


class AllRemindersPerUser(BaseModel):
    """Model for the response of get all reminders."""

    user_id: str
    reminder_title: str
    reminder_id: str
    reminder_tags: Sequence[str]
    reminder_expiration_date_time: Optional[DateTimeUTC]

    model_config = ConfigDict(
        from_attributes=True, json_encoders={datetime.datetime: format_datetime}
    )

    @field_validator("reminder_tags", mode="before")
    def convert_to_list_if_set(cls, value):
        """Convert set to list if needed."""
        return list(value) if isinstance(value, set) else value


class UserDetails(BaseModel):
    """Model for user making the request."""

    user_name: str
    user_email: str


class SingleReminder(ReminderBase):
    """Model for a complete reminder record."""

    reminder_id: str
    user_id: str
    reminder_creation_time: DateTimeUTC


class ShareReminderRequest(BaseModel):
    """Model for share reminder request."""

    username: str

    @field_validator("username")
    def validate_username(cls, value: str) -> str:
        """Validate that the username is not empty."""
        if not value or not value.strip():
            raise ValueError("Username cannot be empty")
        return value.strip()


class CreateReminderRequest(BaseModel):
    """Model for create reminder request."""

    reminder_title: str
    reminder_description: str
    reminder_tags: Sequence[str]
    reminder_frequency: str  # Will be converted to ReminderFrequency enum
    should_expire: bool
    reminder_expiration_date_time: Optional[str] = None
    next_reminder_date_time: Optional[str] = None

    @field_validator("reminder_title")
    def validate_title(cls, value: str) -> str:
        """Validate that the title is not empty or whitespace only."""
        if not value or not value.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return value.strip()


class UpdateReminderRequest(BaseModel):
    """Model for update reminder request (all fields optional)."""

    reminder_title: Optional[str] = None
    reminder_description: Optional[str] = None
    reminder_tags: Optional[Sequence[str]] = None
    reminder_frequency: Optional[str] = None
    should_expire: Optional[bool] = None
    reminder_expiration_date_time: Optional[str] = None
    next_reminder_date_time: Optional[str] = None

    @field_validator("reminder_title")
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        """Validate that the title is not empty or whitespace only."""
        if value is not None and (not value or not value.strip()):
            raise ValueError("Title cannot be empty or whitespace only")
        return value.strip() if value else None


class CreateReminderResponse(BaseModel):
    """Model for create reminder response."""

    reminderId: str
    message: str


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class ReminderIdResponse(BaseModel):
    """Response with reminder ID and message."""

    reminderId: str
    message: str
