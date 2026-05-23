import { useEffect, useState, type FormEvent } from 'react';
import { fetchSettings, updateSettings } from '../api/client';

export function SettingsPanel() {
  const [dailyWordCount, setDailyWordCount] = useState('10');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  async function loadSettings() {
    try {
      setLoading(true);
      setError(null);
      const settings = await fetchSettings();
      setDailyWordCount(String(settings.daily_word_count ?? 10));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load settings.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadSettings(); }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSaved(false);
    const parsedCount = Number(dailyWordCount);
    if (!Number.isInteger(parsedCount) || parsedCount <= 0) {
      setError('Daily word count must be a positive whole number.');
      return;
    }
    try {
      setSubmitting(true);
      const settings = await updateSettings({ daily_word_count: parsedCount });
      setDailyWordCount(String(settings.daily_word_count ?? parsedCount));
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save settings.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="loading">Loading settings...</div>;

  return (
    <section className="form-panel">
      <div className="section-heading"><p className="eyebrow">Review</p><h2>Settings</h2></div>
      <form onSubmit={handleSubmit}>
        <div className="form-group compact-field">
          <label className="form-label" htmlFor="daily-word-count">Daily word count</label>
          <input id="daily-word-count" className="form-input" type="number" min="1" value={dailyWordCount} onChange={(event) => setDailyWordCount(event.target.value)} />
        </div>
        <p className="muted-status">Changes take effect on the next calendar day because today's list is cached.</p>
        {error && <p className="form-error">{error}</p>}
        {saved && <p className="success-text">Settings saved.</p>}
        <div className="form-actions">
          <button type="submit" className="add-btn" disabled={submitting}>{submitting ? 'Saving...' : 'Save Settings'}</button>
          <button type="button" className="close-btn" onClick={loadSettings}>Reload</button>
        </div>
      </form>
    </section>
  );
}
