"""Module for the dynamodb backend interactions."""

from typing import Any, Dict, List

import chalicelib.backend.dynamodb.models as models
from chalicelib.data_structures import SingleReminder


class DynamoBackend:
    @staticmethod
    def create_a_new_reminder(new_reminder: SingleReminder) -> Dict[str, Any]:
        """Create a new reminder using pynamodb."""
        new_reminder = models.Reminders(**new_reminder.dict())
        return new_reminder.save()

    @staticmethod
    def get_all_reminders_for_a_user(user_id: str) -> List[models.Reminders]:
        """Gets all reminders for a user."""
        return list(models.Reminders.view_index.query(user_id))

    @staticmethod
    def get_all_reminders_for_a_user_by_tag(
        user_id: str, tag: str
    ) -> List[models.Reminders]:
        """Gets the reminders for a user but only for a tag."""
        return list(
            models.Reminders.view_index.query(
                user_id, filter_condition=models.Reminders.reminder_tags.contains(tag)
            )
        )

    @staticmethod
    def update_a_reminder(reminder_id: str, updated_reminder: Dict[str, Any]) -> None:
        """Update a reminder."""
        for reminder in models.Reminders.query(reminder_id):
            # try to loop through the reminders
            # since if a reminder has been shared with someone
            # it will have more than 1 entries in the table
            # in which only the user id(range key) is different
            # THIS DOES NOT WORK...CHECK NOTES
            reminder.reminder_title = updated_reminder.get("reminder_title")
            reminder.reminder_description = updated_reminder.get("reminder_description")
            reminder.reminder_tags = updated_reminder.get("reminder_tags")
            reminder.reminder_frequency = updated_reminder.get("reminder_frequency")
            reminder.reminder_expiration_date_time = updated_reminder.get(
                "reminder_expiration_date_time"
            )
            reminder.next_reminder_date_time = updated_reminder.get(
                "next_reminder_date_time"
            )
            reminder.should_expire = updated_reminder.get("should_expire")
            reminder.save()

    @staticmethod
    def get_a_reminder_for_a_user(
        reminder_id: str, user_name: str
    ) -> List[models.Reminders]:
        """Return the details of a reminder."""
        return list(
            models.Reminders.query(
                reminder_id, models.Reminders.user_id.startswith(user_name)
            )
        )

    @staticmethod
    def get_a_reminder_gsi(user_id: str, reminder_title: str):
        """Get a reminder by querying the global secondary index."""
        return models.Reminders.view_index.query(
            user_id, models.Reminders.reminder_title == reminder_title
        )

    @staticmethod
    def delete_a_reminder(reminder_id: str):
        """Deletes a reminder."""
        return list(models.Reminders.query(reminder_id))[0].delete()
