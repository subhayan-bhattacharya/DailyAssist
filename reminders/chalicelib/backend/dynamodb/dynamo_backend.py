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
