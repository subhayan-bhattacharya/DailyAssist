"""Tests for the data structures in the reminders project."""
import pytest
import chalicelib.data_structures as data_structures
import pydantic
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestReminderDetailsFromRequest:
    """Tests for ReminderDetailsFromRequest."""

    def test_normal_object_creation(self):
        """Test that an instance can be created using valid parameters."""
        assert (
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "once",
                    "should_expire": True,
                    "reminder_expiration_date_time": "11/08/23 10:00",
                    "next_reminder_date_time": "11/07/23 08:00",
                }
            )
            is not None
        )

    def test_that_a_past_expiration_date_cannot_be_set(self):
        """Test that you cannot give an expiration date in the past."""
        with pytest.raises(pydantic.error_wrappers.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "once",
                    "should_expire": True,
                    "reminder_expiration_date_time": "11/08/21 10:00",
                    "next_reminder_date_time": "11/07/23 08:00",
                }
            )

    def test_next_reminder_cannot_be_in_the_past(self):
        """Test that the next reminder date cannot be in the past."""
        with pytest.raises(pydantic.error_wrappers.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "once",
                    "should_expire": True,
                    "reminder_expiration_date_time": "11/08/23 10:00",
                    "next_reminder_date_time": "11/07/21 08:00",
                }
            )

    def test_next_reminder_date_cannot_be_later_than_expiration_date(self):
        """Test that the next reminder date cannot be later than the expiration date."""
        with pytest.raises(pydantic.error_wrappers.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "once",
                    "should_expire": True,
                    "reminder_expiration_date_time": "11/08/23 10:00",
                    "next_reminder_date_time": "11/07/25 08:00",
                }
            )

    def test_invalid_value_for_reminder_frequency(self):
        """Test that a reminder cannot be created with an invalid value for reminder frequency."""
        with pytest.raises(pydantic.error_wrappers.ValidationError):
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
        reminder = data_structures.ReminderDetailsFromRequest.parse_obj(
            {
                "reminder_title": "My first reminder!",
                "reminder_description": "Test description.",
                "reminder_tags": ["Test"],
                "reminder_frequency": "daily",
                "should_expire": False,
                "reminder_expiration_date_time": "11/08/23 10:00",
                "next_reminder_date_time": "11/07/23 08:00",
            }
        )
        assert not hasattr(reminder, "reminder_expiration_date_time")

    @pytest.mark.parametrize(
        "frequency, reminder_expiration_date_time_str, next_reminder_date_time_in_str",
        [
            ("once", "11/08/23 10:00", "10/08/23"),
            (
                "daily",
                "11/08/23 10:00",
                # If the reminder frequency is daily then the next reminder is 1 day from today
                datetime.strftime(datetime.now() + relativedelta(days=1), "%d/%m/%y"),
            ),
            (
                "monthly",
                "11/08/23 10:00",
                # If the reminder frequency is monthly then the next reminder is 1 month from today
                datetime.strftime(datetime.now() + relativedelta(months=1), "%d/%m/%y"),
            ),
            (
                "yearly",
                "11/08/23 10:00",
                # If the reminder frequency is monthly then the next reminder is 1 month from today
                datetime.strftime(datetime.now() + relativedelta(years=1), "%d/%m/%y"),
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
            datetime.strftime(reminder.next_reminder_date_time, "%d/%m/%y")
            == next_reminder_date_time_in_str
        )

    def test_for_a_reminder_frequency_of_yearly_the_next_reminder_cannot_be_more_than_expiration(
        self,
    ):
        """For a yearly frequency of reminder the next reminder cannot be more than the given expiration."""
        with pytest.raises(pydantic.error_wrappers.ValidationError):
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
        with pytest.raises(pydantic.error_wrappers.ValidationError):
            data_structures.ReminderDetailsFromRequest.parse_obj(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "yearly",
                    "should_expire": True,
                }
            )
