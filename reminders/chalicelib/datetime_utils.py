"""Utilities for handling datetime operations."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Annotated
from zoneinfo import ZoneInfo

# Type aliases and custom types
DateStr = Annotated[
    str, "Date string in format DD/MM/YY HH:MM or DD Month YYYY, HH:MM AM/PM"
]
"""Type alias for date strings in supported formats."""

DateTimeUTC = Annotated[datetime.datetime, "UTC timezone-aware datetime"]
"""Type alias for UTC timezone-aware datetime objects."""

# Constants
DEFAULT_DATE_FORMATS = [
    "%d/%m/%y %H:%M",  # DD/MM/YY HH:MM
    "%d %B %Y, %I:%M %p",  # DD Month YYYY, HH:MM AM/PM
]
"""Supported date format strings for parsing and formatting."""


@dataclass
class DateTimeConfig:
    """Configuration for datetime handling."""

    timezone: ZoneInfo = field(default_factory=lambda: ZoneInfo("UTC"))
    date_formats: list[str] = field(default_factory=lambda: DEFAULT_DATE_FORMATS.copy())


def parse_datetime(
    value: str | datetime.datetime, config: DateTimeConfig | None = None
) -> DateTimeUTC:
    """Parse a datetime string or convert a datetime to UTC.

    Args:
        value: The datetime string or datetime object to parse/convert
        config: Configuration for datetime parsing

    Returns:
        A UTC timezone-aware datetime

    Raises:
        ValueError: If the datetime string cannot be parsed or is in the past
    """
    if config is None:
        config = DateTimeConfig()

    if isinstance(value, datetime.datetime):
        dt = value
    else:
        # Try each format in sequence
        for fmt in config.date_formats:
            try:
                dt = datetime.datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        else:
            formats_str = '", "'.join(config.date_formats)
            raise ValueError(
                f'Could not parse datetime string "{value}". '
                f'Expected formats: "{formats_str}"'
            )

    # Ensure timezone awareness
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=config.timezone)

    # Convert to UTC
    dt_utc = dt.astimezone(datetime.UTC)

    # Validate not in past
    if dt_utc < datetime.datetime.now(datetime.UTC):
        raise ValueError("Datetime must be in the future")

    return dt_utc


def format_datetime(dt: DateTimeUTC, format: str = "%d %B %Y, %I:%M %p") -> str:
    """Format a datetime object to string.

    Args:
        dt: The datetime to format
        format: The format string to use

    Returns:
        A formatted datetime string
    """
    return dt.strftime(format).replace(" 0", " ")
