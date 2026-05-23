import { useCallback, useEffect, useState } from 'react';
import { fetchExamples, isApiError } from '../api/client';
import type { ExamplesResponse } from '../api/types';

interface ExamplesPanelProps {
  wordId: string;
}

export function ExamplesPanel({ wordId }: ExamplesPanelProps) {
  const [examples, setExamples] = useState<ExamplesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadExamples = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setExamples(await fetchExamples(wordId));
    } catch (err) {
      if (isApiError(err) && err.status === 404) {
        setError('No examples are available for this word yet.');
      } else {
        setError(err instanceof Error ? err.message : 'Could not load examples.');
      }
    } finally {
      setLoading(false);
    }
  }, [wordId]);

  useEffect(() => {
    loadExamples();
  }, [loadExamples]);

  return (
    <section className="examples-panel" aria-live="polite">
      <div className="examples-header">
        <h3>Examples</h3>
        <button type="button" className="close-btn" onClick={loadExamples} disabled={loading}>Refresh</button>
      </div>
      {loading && <p className="muted-status">Loading examples...</p>}
      {error && <p className="form-error">{error}</p>}
      {examples && (
        <ol className="examples-list">
          {examples.sentences.map((sentence, index) => (
            <li key={`${sentence.sentence_de}-${index}`} className="example-row">
              <p className="sentence-de">{sentence.sentence_de}</p>
              <p className="sentence-en">{sentence.sentence_en}</p>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
