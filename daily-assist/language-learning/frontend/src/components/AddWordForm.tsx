import { useState, type FormEvent } from 'react';
import { createWord, isApiError } from '../api/client';
import type { WordResponse } from '../api/types';

export function AddWordForm() {
  const [germanWord, setGermanWord] = useState('');
  const [meaning, setMeaning] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdWord, setCreatedWord] = useState<WordResponse | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setCreatedWord(null);

    if (!germanWord.trim()) {
      setError('German word is required.');
      return;
    }

    try {
      setSubmitting(true);
      const word = await createWord({
        german_word: germanWord.trim(),
        meaning: meaning.trim() || undefined,
        notes: notes.trim() || undefined,
      });
      setCreatedWord(word);
      setGermanWord('');
      setMeaning('');
      setNotes('');
    } catch (err) {
      setError(isApiError(err) && err.status === 409 ? 'This word already exists.' : err instanceof Error ? err.message : 'Could not add the word.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="form-panel">
      <div className="section-heading"><p className="eyebrow">Vocabulary</p><h2>Add Word</h2></div>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="german-word">German word or phrase</label>
          <input id="german-word" className="form-input" value={germanWord} onChange={(event) => setGermanWord(event.target.value)} placeholder="die Geselligkeit" />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="meaning">Meaning</label>
          <input id="meaning" className="form-input" value={meaning} onChange={(event) => setMeaning(event.target.value)} placeholder="sociability" />
        </div>
        <div className="form-group">
          <label className="form-label" htmlFor="notes">Notes</label>
          <textarea id="notes" className="form-textarea" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="noun, phrase, takes dative..." rows={3} />
        </div>
        {error && <p className="form-error">{error}</p>}
        <div className="form-actions"><button type="submit" className="add-btn" disabled={submitting}>{submitting ? 'Adding...' : 'Add Word'}</button></div>
      </form>
      {createdWord && (
        <div className="success-panel">
          <h3>{createdWord.german_word}</h3>
          <p>Status: <strong>{createdWord.enrichment_status}</strong></p>
          {createdWord.enrichment_status === 'pending' && <p>Examples will appear after the enrichment job has processed this word.</p>}
        </div>
      )}
    </section>
  );
}
