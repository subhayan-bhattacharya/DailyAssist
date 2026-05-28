import { requestJson } from '../../../../shared/frontend/http';
import type { Reminder, ReminderDetail, ReminderPayload } from './types';

const remindersApiUrl = import.meta.env.VITE_REMINDERS_API_URL
  ?? import.meta.env.VITE_API_URL
  ?? 'http://127.0.0.1:8001';

export function getRemindersApiBaseUrl(): string {
  return remindersApiUrl;
}

export async function fetchReminders(): Promise<Reminder[]> {
  const reminders = await requestJson<Reminder[]>(remindersApiUrl, '/reminders');
  return reminders.sort((a, b) => {
    if (a.reminder_expiration_date_time === null && b.reminder_expiration_date_time === null) return 0;
    if (a.reminder_expiration_date_time === null) return 1;
    if (b.reminder_expiration_date_time === null) return -1;
    return new Date(a.reminder_expiration_date_time).getTime() - new Date(b.reminder_expiration_date_time).getTime();
  });
}

export function fetchReminderDetail(reminderId: string): Promise<ReminderDetail> {
  return requestJson<ReminderDetail>(remindersApiUrl, `/reminders/${reminderId}`);
}

export function createReminder(payload: ReminderPayload): Promise<unknown> {
  return requestJson(remindersApiUrl, '/reminders', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateReminder(reminderId: string, payload: ReminderPayload): Promise<unknown> {
  return requestJson(remindersApiUrl, `/reminders/${reminderId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteReminder(reminderId: string): Promise<unknown> {
  return requestJson(remindersApiUrl, `/reminders/${reminderId}`, {
    method: 'DELETE',
  });
}
