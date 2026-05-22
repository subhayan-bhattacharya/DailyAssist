import { useEffect, useState, type FormEvent } from 'react';
import { createDefaultPrompt, fetchDefaultPrompt, isApiError } from '../api/client';

export function PromptEditor() {
  const [name, setName] = useState('');
  const [template, setTemplate] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [emptyPrompt, setEmptyPrompt] = useState(false);

  async function loadPrompt() {
    try {
      setLoading(true);
      setError(null);
      setSaved(false);
      const prompt = await fetchDefaultPrompt();
      setName(prompt.name);
      setTemplate(prompt.template);
      setEmptyPrompt(false);
    } catch (err) {
      if (isApiError(err) && err.status === 404) {
        setName('');
        setTemplate('');
        setEmptyPrompt(true);
      } else {
        setError(err instanceof Error ? err.message : 'Could not load prompt.');
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadPrompt(); }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSaved(false);
    if (!name.trim()) {
      setError('Prompt name is required.');
      return;
    }
    if (!template.includes('{{word}}')) {
      setError('Prompt template must include the {{word}} placeholder.');
      return;
    }
    try {
      setSubmitting(true);
      const prompt = await createDefaultPrompt({ name: name.trim(), template });
      setName(prompt.name);
      setTemplate(prompt.template);
      setEmptyPrompt(false);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save prompt.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="loading">Loading prompt...</div>;

  return (
    <section className="form-panel prompt-panel">
      <div className="section-heading"><p className="eyebrow">Enrichment</p><h2>Default Prompt</h2></div>
      {emptyPrompt && <div className="notice-panel">No default prompt is configured yet. Create one for future enrichment jobs.</div>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="prompt-name">Prompt name</label>
          <input id="prompt-name" className="form-input" value={name} onChange={(event) => setName(event.target.value)} placeholder="b2_tutor_prompt_v2" />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="prompt-template">Template</label>
          <textarea id="prompt-template" className="form-textarea prompt-textarea" value={template} onChange={(event) => setTemplate(event.target.value)} placeholder="Explain {{word}} with examples..." rows={14} />
        </div>
        <p className="muted-status">The template must include <code>{'{{word}}'}</code>.</p>
        {error && <p className="form-error">{error}</p>}
        {saved && <p className="success-text">Default prompt saved.</p>}
        <div className="form-actions">
          <button type="submit" className="add-btn" disabled={submitting}>{submitting ? 'Saving...' : 'Save Prompt'}</button>
          <button type="button" className="close-btn" onClick={loadPrompt}>Reload</button>
        </div>
      </form>
    </section>
  );
}
