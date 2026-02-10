import { useState, type FormEvent } from 'react';
import { getAuthToken } from '../utils/auth';
import { formatToBackendDateTime, toDatetimeLocalValue } from '../utils/date';

interface ReminderDetail {
  reminder_id: string;
  reminder_title: string;
  reminder_description: string;
  reminder_tags: string[];
  reminder_frequency: string;
  should_expire: boolean;
  reminder_expiration_date_time: string | null;
  next_reminder_date_time: string | null;
}

interface EditReminderFormProps {
  reminder: ReminderDetail;
  onSuccess: () => void;
  onCancel: () => void;
}

export function EditReminderForm({ reminder, onSuccess, onCancel }: EditReminderFormProps) {
  const [title, setTitle] = useState(reminder.reminder_title);
  const [description, setDescription] = useState(reminder.reminder_description);
  const [tags, setTags] = useState(reminder.reminder_tags.join(', '));
  const [frequency, setFrequency] = useState(reminder.reminder_frequency);
  const [shouldExpire, setShouldExpire] = useState(reminder.should_expire);
  const [expirationDateTime, setExpirationDateTime] = useState(
    reminder.reminder_expiration_date_time
      ? toDatetimeLocalValue(reminder.reminder_expiration_date_time)
      : ''
  );
  const [nextReminderDateTime, setNextReminderDateTime] = useState(
    reminder.next_reminder_date_time
      ? toDatetimeLocalValue(reminder.next_reminder_date_time)
      : ''
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = import.meta.env.VITE_API_URL;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!title.trim()) {
      setError('Title is required.');
      return;
    }
    if (!description.trim()) {
      setError('Description is required.');
      return;
    }
    if (shouldExpire && !expirationDateTime) {
      setError('Expiration date is required when "Should Expire" is checked.');
      return;
    }

    const parsedTags = tags
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    const body: Record<string, unknown> = {
      reminder_title: title.trim(),
      reminder_description: description.trim(),
      reminder_tags: parsedTags,
      reminder_frequency: frequency,
      should_expire: shouldExpire,
    };

    if (shouldExpire && expirationDateTime) {
      body.reminder_expiration_date_time = formatToBackendDateTime(expirationDateTime);
    }

    if (nextReminderDateTime) {
      body.next_reminder_date_time = formatToBackendDateTime(nextReminderDateTime);
    }

    try {
      setSubmitting(true);
      const token = await getAuthToken();
      const response = await fetch(`${apiUrl}/reminders/${reminder.reminder_id}`, {
        method: 'PUT',
        headers: {
          'Authorization': token,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to update reminder: ${response.status} - ${errorText}`);
      }

      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="add-form">
      <h3>Edit Reminder</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="edit-title">Title</label>
          <input
            id="edit-title"
            className="form-input"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="edit-description">Description</label>
          <textarea
            id="edit-description"
            className="form-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="edit-tags">Tags (comma-separated)</label>
          <input
            id="edit-tags"
            className="form-input"
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="edit-frequency">Frequency</label>
          <select
            id="edit-frequency"
            className="form-select"
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
          >
            <option value="once">Once</option>
            <option value="daily">Daily</option>
            <option value="monthly">Monthly</option>
            <option value="yearly">Yearly</option>
          </select>
        </div>

        <div className="form-checkbox-row">
          <input
            id="edit-should-expire"
            type="checkbox"
            checked={shouldExpire}
            onChange={(e) => setShouldExpire(e.target.checked)}
          />
          <label htmlFor="edit-should-expire">Should Expire</label>
        </div>

        {shouldExpire && (
          <div className="form-group">
            <label className="form-label" htmlFor="edit-expiration">Expiration Date *</label>
            <input
              id="edit-expiration"
              className="form-input"
              type="datetime-local"
              value={expirationDateTime}
              onChange={(e) => setExpirationDateTime(e.target.value)}
            />
          </div>
        )}

        <div className="form-group">
          <label className="form-label" htmlFor="edit-next">Next Reminder Date (optional)</label>
          <input
            id="edit-next"
            className="form-input"
            type="datetime-local"
            value={nextReminderDateTime}
            onChange={(e) => setNextReminderDateTime(e.target.value)}
          />
        </div>

        {error && <p className="form-error">{error}</p>}

        <div className="form-actions">
          <button type="submit" className="add-btn" disabled={submitting}>
            {submitting ? 'Saving...' : 'Save Changes'}
          </button>
          <button type="button" className="close-btn" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
