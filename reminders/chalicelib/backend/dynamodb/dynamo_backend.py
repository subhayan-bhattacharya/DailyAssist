"""Module for the dynamodb backend interactions."""

from typing import Any, Dict, List

import chalicelib.backend.dynamodb.models as models
from chalicelib.data_structures import NewReminder


class DynamoBackend:
    @staticmethod
    def create_a_new_reminder(new_reminder: NewReminder) -> Dict[str, Any]:
        """Create a new reminder using pynamodb."""
        new_reminder = models.Reminders(**new_reminder.dict())
        return new_reminder.save()

    @staticmethod
    def get_all_reminders_for_a_user(user_id: str) -> List[models.Reminders]:
        """Gets all reminders for a user."""
        return list(models.Reminders.view_index.query(user_id))

    @staticmethod
    def get_a_reminder(reminder_id: str) -> Dict[str, Any]:
        """Return the details of a reminder."""
        pass

    @staticmethod
    def get_a_reminder_gsi(user_id: str, reminder_title: str):
        """Get a reminder by querying the global secondary index."""
        return models.Reminders.view_index.query(user_id, models.Reminders.reminder_title == reminder_title)

