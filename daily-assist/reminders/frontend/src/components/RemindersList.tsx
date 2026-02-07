import { useState, useEffect } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';

interface Reminder {
  reminder_id: string;
  reminder_title: string;
  reminder_tags: string[];
  reminder_expiration_date_time: string | null;
}

interface ReminderDetail {
  reminder_id: string;
  reminder_title: string;
  reminder_description: string;
  reminder_tags: string[];
  reminder_frequency: string;
  should_expire: boolean;
  reminder_expiration_date_time: string | null;
  next_reminder_date_time: string | null;
  reminder_creation_time: string;
}

function formatDate(value: string): string {
  const date = new Date(value);
  const day = date.getDate();
  const suffix = [11, 12, 13].includes(day) ? 'th'
    : day % 10 === 1 ? 'st'
    : day % 10 === 2 ? 'nd'
    : day % 10 === 3 ? 'rd' : 'th';
  const month = date.toLocaleString('en-US', { month: 'long' });
  const year = date.getFullYear();
  const time = date.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  return `${day}${suffix} of ${month} ${year}, ${time}`;
}

async function getAuthToken(): Promise<string> {
  const session = await fetchAuthSession();
  const token = session.tokens?.idToken?.toString();
  if (!token) {
    throw new Error('No authentication token available');
  }
  return token;
}

export function RemindersList() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [selectedReminder, setSelectedReminder] = useState<ReminderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = import.meta.env.VITE_API_URL;

  useEffect(() => {
    fetchReminders();
  }, []);

  async function fetchReminders() {
    try {
      setLoading(true);
      setError(null);
      setSelectedReminder(null);

      const token = await getAuthToken();
      const response = await fetch(`${apiUrl}/reminders`, {
        headers: {
          'Authorization': token,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch reminders: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      setReminders(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }

  async function fetchReminderDetail(reminderId: string) {
    try {
      setDetailLoading(true);
      setError(null);

      const token = await getAuthToken();
      const response = await fetch(`${apiUrl}/reminders/${reminderId}`, {
        headers: {
          'Authorization': token,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch reminder: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      setSelectedReminder(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setDetailLoading(false);
    }
  }

  if (loading) {
    return <div className="loading">Loading reminders...</div>;
  }

  if (error) {
    return (
      <div className="error">
        <p>Error: {error}</p>
        <button onClick={fetchReminders}>Retry</button>
      </div>
    );
  }

  if (reminders.length === 0) {
    return <div className="empty">No reminders found. Create your first reminder!</div>;
  }

  return (
    <div className="reminders-list">
      <div className="reminders-header">
        <h2>Your Reminders</h2>
        <button onClick={fetchReminders} className="refresh-btn">Refresh</button>
      </div>
      <ul>
        {reminders.map((reminder) => (
          <li
            key={reminder.reminder_id}
            className={`reminder-item ${selectedReminder?.reminder_id === reminder.reminder_id ? 'selected' : ''}`}
            onClick={() => fetchReminderDetail(reminder.reminder_id)}
          >
            <div className="reminder-item-content">
              <div className="reminder-item-left">
                <h3>{reminder.reminder_title}</h3>
                {reminder.reminder_expiration_date_time && (
                  <p className="expiration-date">
                    Expires: {formatDate(reminder.reminder_expiration_date_time)}
                  </p>
                )}
              </div>
              {reminder.reminder_tags && reminder.reminder_tags.length > 0 && (
                <div className="reminder-item-tags">
                  {reminder.reminder_tags.map((tag) => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>

      {detailLoading && <div className="loading">Loading details...</div>}

      {selectedReminder && !detailLoading && (
        <div className="reminder-detail">
          <div className="detail-header">
            <h3>{selectedReminder.reminder_title}</h3>
            <button className="close-btn" onClick={() => setSelectedReminder(null)}>Close</button>
          </div>
          <div className="detail-fields">
            <div className="detail-row">
              <span className="detail-label">Description</span>
              <span className="detail-value">{selectedReminder.reminder_description}</span>
            </div>
            <div className="detail-row">
              <span className="detail-label">Frequency</span>
              <span className="detail-value">{selectedReminder.reminder_frequency}</span>
            </div>
            {selectedReminder.next_reminder_date_time && (
              <div className="detail-row">
                <span className="detail-label">Next Reminder</span>
                <span className="detail-value">{formatDate(selectedReminder.next_reminder_date_time)}</span>
              </div>
            )}
            {selectedReminder.reminder_expiration_date_time && (
              <div className="detail-row">
                <span className="detail-label">Expires</span>
                <span className="detail-value">{formatDate(selectedReminder.reminder_expiration_date_time)}</span>
              </div>
            )}
            <div className="detail-row">
              <span className="detail-label">Created</span>
              <span className="detail-value">{formatDate(selectedReminder.reminder_creation_time)}</span>
            </div>
            {selectedReminder.reminder_tags.length > 0 && (
              <div className="detail-row">
                <span className="detail-label">Tags</span>
                <div className="detail-tags">
                  {selectedReminder.reminder_tags.map((tag) => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
