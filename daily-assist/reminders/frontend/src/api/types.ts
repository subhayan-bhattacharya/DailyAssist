export interface Reminder {
  reminder_id: string;
  reminder_title: string;
  reminder_tags: string[];
  reminder_expiration_date_time: string | null;
}

export interface ReminderDetail {
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

export interface ReminderPayload {
  reminder_title: string;
  reminder_description: string;
  reminder_tags: string[];
  reminder_frequency: string;
  should_expire: boolean;
  reminder_expiration_date_time?: string;
  next_reminder_date_time?: string;
}
