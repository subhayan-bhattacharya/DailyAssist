import { useState, useEffect } from 'react';
import { fetchAuthSession } from 'aws-amplify/auth';

interface Reminder {
  reminder_id: string;
  reminder_title: string;
  reminder_description: string;
  reminder_tags: string[];
  reminder_frequency: string;
  next_reminder_date_time: string | null;
  reminder_expiration_date_time: string | null;
}

interface RemindersResponse {
  reminders: Reminder[];
}

export function RemindersList() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReminders();
  }, []);

  async function fetchReminders() {
    try {
      setLoading(true);
      setError(null);

      console.log('Fetching auth session...');
      const session = await fetchAuthSession();
      console.log('Auth session:', session);

      const token = session.tokens?.idToken?.toString();
      console.log('Token available:', !!token);

      if (!token) {
        throw new Error('No authentication token available');
      }

      const apiUrl = import.meta.env.VITE_API_URL;
      console.log('API URL:', apiUrl);
      console.log('Fetching reminders from:', `${apiUrl}/reminders`);

      const response = await fetch(`${apiUrl}/reminders`, {
        headers: {
          'Authorization': token,
          'Content-Type': 'application/json',
        },
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response body:', errorText);
        throw new Error(`Failed to fetch reminders: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('Response data:', data);
      setReminders(data.reminders || data);
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
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
      <h2>Your Reminders</h2>
      <button onClick={fetchReminders} className="refresh-btn">Refresh</button>
      <ul>
        {reminders.map((reminder) => (
          <li key={reminder.reminder_id} className="reminder-item">
            <h3>{reminder.reminder_title}</h3>
            <p>{reminder.reminder_description}</p>
            <div className="reminder-meta">
              <span className="frequency">Frequency: {reminder.reminder_frequency}</span>
              {reminder.next_reminder_date_time && (
                <span className="next-date">
                  Next: {new Date(reminder.next_reminder_date_time).toLocaleString()}
                </span>
              )}
            </div>
            {reminder.reminder_tags && reminder.reminder_tags.length > 0 && (
              <div className="tags">
                {reminder.reminder_tags.map((tag) => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
