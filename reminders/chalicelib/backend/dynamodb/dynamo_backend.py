"""Module for the DynamoDB backend interactions.

This module provides a DynamoBackend class that handles all DynamoDB operations
for the reminders application. It uses PynamoDB models for database interactions.
"""

from typing import Any, Dict, Iterator, List

import chalicelib.backend.dynamodb.models as models
from chalicelib.data_structures import SingleReminder
from pynamodb.exceptions import PynamoDBException


class DynamoDBError(Exception):
    """Base exception for DynamoDB related errors."""

    pass


class ReminderNotFoundError(DynamoDBError):
    """Exception raised when a reminder is not found."""

    pass


class DynamoBackend:
    """Handles all DynamoDB operations for the reminders application."""

    @staticmethod
    def create_a_new_reminder(new_reminder: SingleReminder) -> Dict[str, Any]:
        """Create a new reminder using PynamoDB.

        Args:
            new_reminder: A SingleReminder instance containing the reminder details.

        Returns:
            Dict[str, Any]: The saved reminder data.

        Raises:
            DynamoDBError: If there's an error saving to DynamoDB.
        """
        try:
            # Use Pydantic v2 model_dump() method
            data = new_reminder.model_dump()
            reminder_model = models.Reminders(**data)
            return reminder_model.save()
        except PynamoDBException as e:
            raise DynamoDBError(f"Failed to create reminder: {str(e)}") from e

    @staticmethod
    def get_all_reminders_for_a_user(user_id: str) -> List[models.Reminders]:
        """Gets all reminders for a user.

        Args:
            user_id: The ID of the user whose reminders to retrieve.

        Returns:
            List[models.Reminders]: List of all reminders for the user.

        Raises:
            DynamoDBError: If there's an error querying DynamoDB.
        """
        try:
            return list(models.Reminders.view_index.query(user_id))
        except PynamoDBException as e:
            raise DynamoDBError(f"Failed to get reminders: {str(e)}") from e

    @staticmethod
    def get_all_reminders_for_a_user_by_tag(
        user_id: str, tag: str
    ) -> List[models.Reminders]:
        """Gets the reminders for a user filtered by tag.

        Args:
            user_id: The ID of the user whose reminders to retrieve.
            tag: The tag to filter reminders by.

        Returns:
            List[models.Reminders]: List of filtered reminders.

        Raises:
            DynamoDBError: If there's an error querying DynamoDB.
        """
        try:
            filter_condition = models.Reminders.reminder_tags.contains(tag)
            return list(
                models.Reminders.view_index.query(
                    user_id, filter_condition=filter_condition
                )
            )
        except PynamoDBException as e:
            raise DynamoDBError(f"Failed to get reminders by tag: {str(e)}") from e

    @staticmethod
    def update_a_reminder(reminder_id: str, updated_reminder: Dict[str, Any]) -> None:
        """Update a reminder and all its shared instances.

        This method updates all instances of a reminder that have been shared with
        other users. Each shared reminder has the same reminder_id but different
        user_ids.

        Args:
            reminder_id: The ID of the reminder to update.
            updated_reminder: Dictionary containing the updated reminder data.

        Raises:
            ReminderNotFoundError: If no reminder with the given ID exists.
            DynamoDBError: If there's an error updating the reminder.
        """
        try:
            reminders = list(models.Reminders.query(reminder_id))
            if not reminders:
                raise ReminderNotFoundError(f"No reminder found with ID: {reminder_id}")

            # Get all fields that need to be updated
            update_fields = {
                "reminder_title",
                "reminder_description",
                "reminder_tags",
                "reminder_frequency",
                "reminder_expiration_date_time",
                "next_reminder_date_time",
                "should_expire",
            }

            # Update all instances of the shared reminder
            for reminder in reminders:
                for field in update_fields:
                    if field in updated_reminder:
                        setattr(reminder, field, updated_reminder[field])
                reminder.save()
        except PynamoDBException as e:
            raise DynamoDBError(f"Failed to update reminder: {str(e)}") from e

    @staticmethod
    def get_a_reminder_for_a_user(
        reminder_id: str, user_name: str
    ) -> List[models.Reminders]:
        """Return the details of a reminder for a specific user.

        Args:
            reminder_id: The ID of the reminder to retrieve.
            user_name: The username to filter by.

        Returns:
            List[models.Reminders]: List of matching reminders.

        Raises:
            DynamoDBError: If there's an error querying DynamoDB.
        """
        try:
            return list(
                models.Reminders.query(
                    reminder_id, models.Reminders.user_id.startswith(user_name)
                )
            )
        except PynamoDBException as e:
            raise DynamoDBError(f"Failed to get reminder: {str(e)}") from e

    @staticmethod
    def get_a_reminder_gsi(
        user_id: str, reminder_title: str
    ) -> Iterator[models.Reminders]:
        """Get a reminder by querying the global secondary index.

        Args:
            user_id: The ID of the user whose reminder to retrieve.
            reminder_title: The title of the reminder to retrieve.

        Returns:
            Iterator[models.Reminders]: Iterator of matching reminders.

        Raises:
            DynamoDBError: If there's an error querying DynamoDB.
        """
        try:
            return models.Reminders.view_index.query(
                user_id, models.Reminders.reminder_title == reminder_title
            )
        except PynamoDBException as e:
            raise DynamoDBError(f"Failed to get reminder by GSI: {str(e)}") from e

    @staticmethod
    def delete_a_reminder(reminder_id: str) -> None:
        """Deletes a reminder and all its shared instances.

        Args:
            reminder_id: The ID of the reminder to delete.

        Raises:
            ReminderNotFoundError: If no reminder with the given ID exists.
            DynamoDBError: If there's an error deleting the reminder.
        """
        try:
            reminders = list(models.Reminders.query(reminder_id))
            if not reminders:
                raise ReminderNotFoundError(f"No reminder found with ID: {reminder_id}")

            for reminder in reminders:
                reminder.delete()
        except PynamoDBException as e:
            raise DynamoDBError(f"Failed to delete reminder: {str(e)}") from e
