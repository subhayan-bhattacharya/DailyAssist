"""Module for the dynamodb backend interactions."""

import chalicelib.backend.dynamodb.models as models
from chalicelib.data_structures import NewReminder
from typing import Dict, Any


class DynamoBackend:
    @staticmethod
    def create_a_new_reminder(new_reminder: NewReminder) -> Dict[str, Any]:
        """Create a new reminder using pynamodb."""
        new_reminder = models.Reminders(**new_reminder.dict())
        return new_reminder.save()

    @staticmethod
    def get_a_reminder(reminder_id: str) -> Dict[str, Any]:
        """Return the details of a reminder."""
        pass

    @staticmethod
    def get_a_reminder_gsi(user_id: str, reminder_title: str):
        """Get a reminder by querying the gloabl secondary index."""
        return models.Reminders.view_index.query(user_id, models.Reminders.reminder_title == reminder_title)

