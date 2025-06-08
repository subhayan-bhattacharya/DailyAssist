"""Reminder frequency handling."""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Optional

from dateutil.relativedelta import relativedelta

from chalicelib.datetime_utils import DateTimeUTC


class ReminderFrequency(str, Enum):
    """Reminder frequency enumeration.
    
    Using str as base class for better serialization support.
    """
    ONCE = "once"
    MONTHLY = "monthly"
    DAILY = "daily"
    YEARLY = "yearly"

    def get_next_date(
        self,
        from_date: Optional[DateTimeUTC] = None,
        expiration_date: Optional[DateTimeUTC] = None
    ) -> DateTimeUTC:
        """Calculate the next reminder date based on frequency.
        
        Args:
            from_date: Base date to calculate from. Defaults to current UTC time.
            expiration_date: Optional expiration date to validate against.
            
        Returns:
            The next reminder date
            
        Raises:
            ValueError: If the calculation is invalid (e.g., past date, invalid expiration)
        """
        current_time = from_date or datetime.datetime.now(datetime.UTC)
        
        match self:
            case ReminderFrequency.ONCE:
                if not expiration_date:
                    raise ValueError("Expiration date required for one-time reminders")
                next_date = expiration_date - datetime.timedelta(days=1)
                if current_time > next_date:
                    raise ValueError("Cannot set next reminder in the past")
                return next_date
                
            case ReminderFrequency.DAILY:
                next_date = current_time + relativedelta(days=1)
            case ReminderFrequency.MONTHLY:
                next_date = current_time + relativedelta(months=1)
            case ReminderFrequency.YEARLY:
                next_date = current_time + relativedelta(years=1)
        
        if expiration_date and next_date > expiration_date:
            raise ValueError(
                f"Next reminder date ({next_date}) would be after "
                f"expiration date ({expiration_date})"
            )
        
        return next_date


def calculate_next_reminder_date(
    frequency: ReminderFrequency,
    expiration_date: Optional[DateTimeUTC] = None,
) -> DateTimeUTC:
    """Calculate the next reminder date based on frequency and expiration.
    
    This is a convenience function that calls ReminderFrequency.get_next_date().
    
    Args:
        frequency: The reminder frequency
        expiration_date: Optional expiration date to validate against
        
    Returns:
        The calculated next reminder date
        
    Raises:
        ValueError: If the calculation is invalid for the given frequency/expiration
    """
    return frequency.get_next_date(expiration_date=expiration_date) 