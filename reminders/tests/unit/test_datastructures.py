"""Tests for the data structures in the reminders project."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pydantic
import pytest
from dateutil.relativedelta import relativedelta

import chalicelib.data_structures as data_structures


@pytest.fixture
def base_reminder_data():
    """Fixture providing base reminder data for tests.
    
    Returns:
        dict: A dictionary containing the base reminder data that can be modified for specific tests.
    """
    return {
        "reminder_title": "My first reminder!",
        "reminder_description": "Test description.",
        "reminder_tags": ["Test"],
        "reminder_frequency": "once",
        "should_expire": True,
    }


@pytest.fixture
def future_dates():
    """Fixture providing commonly used future dates for testing.
    
    Returns:
        tuple: A tuple containing (today, next_week, next_month) datetime objects.
    """
    today = datetime.now(ZoneInfo("UTC"))
    return (
        today,
        today + timedelta(days=7),
        today + timedelta(days=30)
    )


class TestReminderDetailsFromRequest:
    """Tests for ReminderDetailsFromRequest.
    
    This test suite verifies the validation and behavior of the ReminderDetailsFromRequest
    data structure, including date handling, frequency validation, and expiration rules.
    """

    def test_normal_object_creation(self, base_reminder_data, future_dates):
        """Test that an instance can be created using valid parameters.
        
        Verifies:
            - Object creation succeeds
            - All fields are correctly set
            - Date formatting is handled properly
        """
        # Arrange
        today, next_week, _ = future_dates
        reminder_data = base_reminder_data.copy()
        reminder_data.update({
            "reminder_expiration_date_time": next_week.strftime("%d/%m/%y %H:%M"),
            "next_reminder_date_time": (today + timedelta(days=5)).strftime("%d/%m/%y %H:%M"),
        })

        # Act
        reminder = data_structures.ReminderDetailsFromRequest.model_validate(reminder_data)

        # Assert
        assert reminder is not None
        assert reminder.reminder_title == reminder_data["reminder_title"]
        assert reminder.reminder_description == reminder_data["reminder_description"]
        assert reminder.reminder_tags == reminder_data["reminder_tags"]
        assert reminder.reminder_frequency.value == reminder_data["reminder_frequency"]
        assert reminder.should_expire == reminder_data["should_expire"]
        assert isinstance(reminder.reminder_expiration_date_time, datetime)
        assert isinstance(reminder.next_reminder_date_time, datetime)

    def test_that_a_past_expiration_date_cannot_be_set(self):
        """Test that you cannot give an expiration date in the past."""
        # Get today's date
        today = datetime.today()
        # Calculate one week earlier
        reminder_expiration_date = today - timedelta(days=7)
        next_reminder_date = today - timedelta(days=5)
        with pytest.raises(pydantic.ValidationError):
            data_structures.ReminderDetailsFromRequest.model_validate(
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
            data_structures.ReminderDetailsFromRequest.model_validate(
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
            data_structures.ReminderDetailsFromRequest.model_validate(
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
            data_structures.ReminderDetailsFromRequest.model_validate(
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
        reminder = data_structures.ReminderDetailsFromRequest.model_validate(
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
                lambda: datetime.now(ZoneInfo("UTC")) + relativedelta(days=20),
                lambda: datetime.now(ZoneInfo("UTC")) + relativedelta(days=19)
            ),
            (
                "daily",
                lambda: datetime.now(ZoneInfo("UTC")) + relativedelta(days=20),
                lambda: datetime.now(ZoneInfo("UTC")) + relativedelta(days=1)
            ),
            (
                "monthly",
                lambda: datetime.now(ZoneInfo("UTC")) + relativedelta(months=4),
                lambda: datetime.now(ZoneInfo("UTC")) + relativedelta(months=1)
            ),
            (
                "yearly",
                lambda: datetime.now(ZoneInfo("UTC")) + relativedelta(years=10),
                lambda: datetime.now(ZoneInfo("UTC")) + relativedelta(years=1)
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
        # Get the actual datetime values from the lambda functions
        expiration_dt = reminder_expiration_date_time_str()
        next_dt = next_reminder_date_time_in_str()
        
        # Format them in the expected string format
        expiration_str = expiration_dt.strftime("%d/%m/%y %H:%M")
        next_dt_str = next_dt.strftime("%d/%m/%y %H:%M")
        
        reminder = data_structures.ReminderDetailsFromRequest.model_validate(
            {
                "reminder_title": "My first reminder!",
                "reminder_description": "Test description.",
                "reminder_tags": ["Test"],
                "reminder_frequency": frequency,
                "should_expire": True,
                "reminder_expiration_date_time": expiration_str,
            }
        )
        
        # Format the actual next reminder time in UTC for comparison
        actual_next_dt_str = reminder.next_reminder_date_time.strftime("%d/%m/%y %H:%M")
        assert actual_next_dt_str == next_dt_str

    def test_for_a_reminder_frequency_of_yearly_the_next_reminder_cannot_be_more_than_expiration(
        self,
    ):
        """For a yearly frequency of reminder the next reminder cannot be more than the given expiration."""
        with pytest.raises(pydantic.ValidationError):
            data_structures.ReminderDetailsFromRequest.model_validate(
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
            data_structures.ReminderDetailsFromRequest.model_validate(
                {
                    "reminder_title": "My first reminder!",
                    "reminder_description": "Test description.",
                    "reminder_tags": ["Test"],
                    "reminder_frequency": "yearly",
                    "should_expire": True,
                }
            )

    def test_empty_title_raises_validation_error(self, base_reminder_data, future_dates):
        """Test that an empty title raises a validation error.
        
        Verifies that the title field cannot be empty or just whitespace.
        """
        # Arrange
        _, next_week, _ = future_dates
        reminder_data = base_reminder_data.copy()
        reminder_data.update({
            "reminder_title": "",  # Empty title
            "reminder_expiration_date_time": next_week.strftime("%d/%m/%y %H:%M"),
        })

        # Act & Assert
        with pytest.raises(pydantic.ValidationError) as exc_info:
            data_structures.ReminderDetailsFromRequest.model_validate(reminder_data)
        assert "reminder_title" in str(exc_info.value)

    def test_whitespace_title_raises_validation_error(self, base_reminder_data, future_dates):
        """Test that a whitespace-only title raises a validation error."""
        # Arrange
        _, next_week, _ = future_dates
        reminder_data = base_reminder_data.copy()
        reminder_data.update({
            "reminder_title": "   ",  # Whitespace title
            "reminder_expiration_date_time": next_week.strftime("%d/%m/%y %H:%M"),
        })

        # Act & Assert
        with pytest.raises(pydantic.ValidationError) as exc_info:
            data_structures.ReminderDetailsFromRequest.model_validate(reminder_data)
        assert "reminder_title" in str(exc_info.value)

    def test_empty_tags_list_is_valid(self, base_reminder_data, future_dates):
        """Test that an empty tags list is valid.
        
        Verifies that reminders can be created without any tags.
        """
        # Arrange
        _, next_week, _ = future_dates
        reminder_data = base_reminder_data.copy()
        reminder_data.update({
            "reminder_tags": [],
            "reminder_expiration_date_time": next_week.strftime("%d/%m/%y %H:%M"),
        })

        # Act
        reminder = data_structures.ReminderDetailsFromRequest.model_validate(reminder_data)

        # Assert
        assert reminder.reminder_tags == []

    @pytest.mark.parametrize("invalid_frequency", [
        "",
        "weekly",  # Assuming this is not a valid frequency
        "bi-monthly",
        "every-day",
        None,
    ])
    def test_invalid_frequencies(self, base_reminder_data, future_dates, invalid_frequency):
        """Test that invalid frequencies raise validation errors.
        
        Args:
            invalid_frequency: Various invalid frequency values to test.
        
        Verifies that only allowed frequency values are accepted.
        """
        # Arrange
        _, next_week, _ = future_dates
        reminder_data = base_reminder_data.copy()
        reminder_data.update({
            "reminder_frequency": invalid_frequency,
            "reminder_expiration_date_time": next_week.strftime("%d/%m/%y %H:%M"),
        })

        # Act & Assert
        with pytest.raises(pydantic.ValidationError) as exc_info:
            data_structures.ReminderDetailsFromRequest.model_validate(reminder_data)
        assert "reminder_frequency" in str(exc_info.value)
