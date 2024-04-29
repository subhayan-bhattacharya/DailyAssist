"""Tests for the data structures in the reminders project."""
from datetime import datetime, timedelta

import pydantic
import pytest
from dateutil.relativedelta import relativedelta

import chalicelib.data_structures as data_structures


class TestReminderDetailsFromRequest:
    """Tests for ReminderDetailsFromRequest."""

    def test_normal_object_creation(self):
        """Test that an instance can be created using valid parameters."""
        # Get today's date
        today = datetime.today()
        # Calculate one week later
        reminder_expiration_date = today + timedelta(days=7)
        next_reminder_date = today + timedelta(days=5)
        assert (
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "once",
                    "should_expire": True,
                    "reminder_expiration_date_time": reminder_expiration_date.strftime("%d/%m/%y %H:%M"),
                    "next_reminder_date_time": next_reminder_date.strftime("%d/%m/%y %H:%M"),
                }
            )
            is not None
        )

    def test_that_a_past_expiration_date_cannot_be_set(self):
        """Test that you cannot give an expiration date in the past."""
        # Get today's date
        today = datetime.today()
        # Calculate one week earlier
        reminder_expiration_date = today - timedelta(days=7)
        next_reminder_date = today - timedelta(days=5)
        with pytest.raises(pydantic.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "once",
                    "should_expire": True,
                    "reminder_expiration_date_time": reminder_expiration_date.strftime("%d/%m/%y %H:%M"),
                    "next_reminder_date_time": next_reminder_date.strftime("%d/%m/%y %H:%M"),
                }
            )

    def test_next_reminder_cannot_be_in_the_past(self):
        """Test that the next reminder date cannot be in the past."""
        # Get today's date
        today = datetime.today()
        # Calculate one week later
        reminder_expiration_date = today + timedelta(days=7)
        next_reminder_date = today - timedelta(days=5)
        with pytest.raises(pydantic.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "once",
                    "should_expire": True,
                    "reminder_expiration_date_time": reminder_expiration_date.strftime("%d/%m/%y %H:%M"),
                    "next_reminder_date_time": next_reminder_date.strftime("%d/%m/%y %H:%M"),
                }
            )

    def test_next_reminder_date_cannot_be_later_than_expiration_date(self):
        """Test that the next reminder date cannot be later than the expiration date."""
        # Get today's date
        today = datetime.today()
        # Calculate one week later
        reminder_expiration_date = today + timedelta(days=7)
        next_reminder_date = today + timedelta(days=8)
        with pytest.raises(pydantic.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "once",
                    "should_expire": True,
                    "reminder_expiration_date_time": reminder_expiration_date.strftime("%d/%m/%y %H:%M"),
                    "next_reminder_date_time": next_reminder_date.strftime("%d/%m/%y %H:%M"),
                }
            )

    def test_invalid_value_for_reminder_frequency(self):
        """Test that a reminder cannot be created with an invalid value for reminder frequency."""
        with pytest.raises(pydantic.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "sometimes",
                    "should_expire": True,
                    "reminder_expiration_date_time": "11/08/23 10:00",
                    "next_reminder_date_time": "11/07/23 08:00",
                }
            )

    def test_when_a_reminder_should_not_expire_there_is_no_expiration_date(self):
        """When the should_expire value is False there is no expiration date."""
        # Get today's date
        today = datetime.today()
        # Calculate one week later
        reminder_expiration_date = today + timedelta(days=7)
        next_reminder_date = today + timedelta(days=5)
        reminder = data_structures.ReminderDetailsFromRequest.parse_obj(
            {
                "reminder_title": "My first reminder!",
                "reminder_description": "Test description.",
                "reminder_tags": ["Test"],
                "reminder_frequency": "daily",
                "should_expire": False,
                "reminder_expiration_date_time": reminder_expiration_date.strftime("%d/%m/%y %H:%M"),
                "next_reminder_date_time": next_reminder_date.strftime("%d/%m/%y %H:%M"),
            }
        )
        assert not hasattr(reminder, "reminder_expiration_date_time")

    @pytest.mark.parametrize(
        "frequency, reminder_expiration_date_time_str, next_reminder_date_time_in_str",
        [
            (
                "once",
                datetime.strftime(datetime.now() + relativedelta(days=20), "%d/%m/%y %H:%M"),
                datetime.strftime(datetime.now() + relativedelta(days=19), "%d/%m/%y %H:%M")
            ),
            (
                "daily",
                datetime.strftime(datetime.now() + relativedelta(days=20), "%d/%m/%y %H:%M"),
                # If the reminder frequency is daily then the next reminder is 1 day from today
                datetime.strftime(datetime.now() + relativedelta(days=1), "%d/%m/%y %H:%M"),
            ),
            (
                "monthly",
                datetime.strftime(datetime.now() + relativedelta(months=4), "%d/%m/%y %H:%M"),
                # If the reminder frequency is monthly then the next reminder is 1 month from today
                datetime.strftime(datetime.now() + relativedelta(months=1), "%d/%m/%y %H:%M"),
            ),
            (
                "yearly",
                datetime.strftime(datetime.now() + relativedelta(years=10), "%d/%m/%y %H:%M"),
                # If the reminder frequency is yearly then the next reminder is 1 year from today
                datetime.strftime(datetime.now() + relativedelta(years=1), "%d/%m/%y %H:%M"),
            ),
        ],
    )
    def test_calculation_of_next_reminder_date(
        self,
        frequency,
        reminder_expiration_date_time_str,
        next_reminder_date_time_in_str,
    ):
        """Test that the calculations of next reminder date and time works."""
        reminder = data_structures.ReminderDetailsFromRequest.parse_obj(
            {
                "reminder_title": "My first reminder!",
                "reminder_description": "Test description.",
                "reminder_tags": ["Test"],
                "reminder_frequency": frequency,
                "should_expire": True,
                "reminder_expiration_date_time": reminder_expiration_date_time_str,
            }
        )
        assert (
            datetime.strftime(reminder.next_reminder_date_time, "%d/%m/%y %H:%M")
            == next_reminder_date_time_in_str
        )

    def test_for_a_reminder_frequency_of_yearly_the_next_reminder_cannot_be_more_than_expiration(
        self,
    ):
        """For a yearly frequency of reminder the next reminder cannot be more than the given expiration."""
        with pytest.raises(pydantic.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "yearly",
                    "should_expire": True,
                    "reminder_expiration_date_time": "11/06/23 10:00",
                }
            )

    def test_when_a_reminder_should_expire_an_expiration_date_is_given(self):
        """When a reminder should expire we should provide an expiration date."""
        with pytest.raises(pydantic.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "yearly",
                    "should_expire": True,
                }
            )
