import { useState, type FormEvent } from 'react';
import { getAuthToken } from '../utils/auth';
import { formatToBackendDateTime } from '../utils/date';

interface AddReminderFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function AddReminderForm({ onSuccess, onCancel }: AddReminderFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [frequency, setFrequency] = useState<string>('once');
  const [shouldExpire, setShouldExpire] = useState(true);
  const [expirationDateTime, setExpirationDateTime] = useState('');
  const [nextReminderDateTime, setNextReminderDateTime] = useState('');
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
      const response = await fetch(`${apiUrl}/reminders`, {
        method: 'POST',
        headers: {
          'Authorization': token,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to create reminder: ${response.status} - ${errorText}`);
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
      <h3>Add Reminder</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="reminder-title">Title</label>
          <input
            id="reminder-title"
            className="form-input"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Reminder title"
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="reminder-description">Description</label>
          <textarea
            id="reminder-description"
            className="form-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Reminder description"
            rows={3}
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="reminder-tags">Tags (comma-separated)</label>
          <input
            id="reminder-tags"
            className="form-input"
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="e.g. work, personal, urgent"
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="reminder-frequency">Frequency</label>
          <select
            id="reminder-frequency"
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
            id="reminder-should-expire"
            type="checkbox"
            checked={shouldExpire}
            onChange={(e) => setShouldExpire(e.target.checked)}
          />
          <label htmlFor="reminder-should-expire">Should Expire</label>
        </div>

        {shouldExpire && (
          <div className="form-group">
            <label className="form-label" htmlFor="reminder-expiration">Expiration Date *</label>
            <input
              id="reminder-expiration"
              className="form-input"
              type="datetime-local"
              value={expirationDateTime}
              onChange={(e) => setExpirationDateTime(e.target.value)}
            />
          </div>
        )}

        <div className="form-group">
          <label className="form-label" htmlFor="reminder-next">Next Reminder Date (optional)</label>
          <input
            id="reminder-next"
            className="form-input"
            type="datetime-local"
            value={nextReminderDateTime}
            onChange={(e) => setNextReminderDateTime(e.target.value)}
          />
        </div>

        {error && <p className="form-error">{error}</p>}

        <div className="form-actions">
          <button type="submit" className="add-btn" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create Reminder'}
          </button>
          <button type="button" className="close-btn" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
