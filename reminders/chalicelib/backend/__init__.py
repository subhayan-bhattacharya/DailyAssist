"""Main module for handling backend related interactions."""
import typing
from typing import Protocol


class ReminderBackend(Protocol):
    """Define protocol class for the backend."""
    def retrieve_all_reminders(self) -> typing.List[typing.Dict[str, typing.Any]]:
        """Retrieve all reminders."""
        pass

    def create_a_new_reminder(self) -> typing.Dict[str, str]:
        """Create a new reminder."""
        pass
