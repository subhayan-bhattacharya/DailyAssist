import { useState, useEffect } from 'react';
import { getAuthToken } from '../utils/auth';
import { AddReminderForm } from './AddReminderForm';
import { EditReminderForm } from './EditReminderForm';

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

export function RemindersList() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [selectedReminder, setSelectedReminder] = useState<ReminderDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingReminder, setEditingReminder] = useState<ReminderDetail | null>(null);

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
      data.sort((a: Reminder, b: Reminder) => {
        if (a.reminder_expiration_date_time === null && b.reminder_expiration_date_time === null) return 0;
        if (a.reminder_expiration_date_time === null) return 1;
        if (b.reminder_expiration_date_time === null) return -1;
        return new Date(a.reminder_expiration_date_time).getTime() - new Date(b.reminder_expiration_date_time).getTime();
      });
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

  async function startEditing(reminderId: string) {
    try {
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
      setEditingReminder(data);
      setSelectedReminder(null);
      setShowAddForm(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  }

  async function deleteReminder(reminderId: string) {
    if (!confirm('Are you sure you want to delete this reminder?')) {
      return;
    }
    try {
      setError(null);
      const token = await getAuthToken();
      const response = await fetch(`${apiUrl}/reminders/${reminderId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': token,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to delete reminder: ${response.status} - ${errorText}`);
      }

      if (selectedReminder?.reminder_id === reminderId) {
        setSelectedReminder(null);
      }
      fetchReminders();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
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
        <div className="header-actions">
          <button onClick={() => setShowAddForm(true)} className="add-btn">Add Reminder</button>
          <button onClick={fetchReminders} className="refresh-btn">Refresh</button>
        </div>
      </div>

      {showAddForm && (
        <AddReminderForm
          onSuccess={() => {
            setShowAddForm(false);
            fetchReminders();
          }}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      {editingReminder && (
        <EditReminderForm
          reminder={editingReminder}
          onSuccess={() => {
            setEditingReminder(null);
            fetchReminders();
          }}
          onCancel={() => setEditingReminder(null)}
        />
      )}

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
              <div className="reminder-item-actions">
                <button
                  className="edit-btn"
                  title="Edit reminder"
                  onClick={(e) => {
                    e.stopPropagation();
                    startEditing(reminder.reminder_id);
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M12.146.854a.5.5 0 0 1 .708 0l2.292 2.292a.5.5 0 0 1 0 .708l-9.5 9.5a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l9.5-9.5zM11.207 2.5L13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5z"/>
                  </svg>
                </button>
                <button
                  className="delete-btn"
                  title="Delete reminder"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteReminder(reminder.reminder_id);
                  }}
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M5.5 5.5a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                    <path fillRule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4L4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                  </svg>
                </button>
              </div>
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
