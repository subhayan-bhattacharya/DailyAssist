import { useState, type FormEvent } from 'react';
import { searchWords } from '../api/client';
import type { WordSearchResult } from '../api/types';
import { ExamplesPanel } from './ExamplesPanel';

function formatCreatedAt(value: string): string {
  return new Date(value).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function getStatusClass(status: string): string {
  if (status === 'completed') return 'status-completed';
  if (status === 'failed') return 'status-failed';
  if (status === 'processing') return 'status-processing';
  return 'status-pending';
}

export function WordSearch() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<WordSearchResult[]>([]);
  const [searchedQuery, setSearchedQuery] = useState('');
  const [expandedWordId, setExpandedWordId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function handleSearch(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setExpandedWordId(null);

    const trimmedQuery = query.trim();
    if (!trimmedQuery) {
      setError('Enter a full word or any part of it.');
      return;
    }

    try {
      setLoading(true);
      const response = await searchWords(trimmedQuery);
      setResults(response.words);
      setSearchedQuery(response.query);
      setHasSearched(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not search words.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="search-panel">
      <div className="section-heading">
        <p className="eyebrow">Vocabulary</p>
        <h2>Search Words</h2>
      </div>

      <form className="search-form" onSubmit={handleSearch}>
        <div className="search-input-wrap">
          <label className="form-label" htmlFor="word-search">Word or substring</label>
          <input
            id="word-search"
            className="form-input search-input"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="gesell, ruh, außergewöhnlich..."
          />
        </div>
        <button type="submit" className="add-btn search-submit" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {error && <p className="form-error">{error}</p>}

      {!hasSearched && (
        <div className="search-empty">
          <h3>Check before adding</h3>
          <p>Search by a full German word, phrase, or any substring to see whether it already exists and whether examples are available.</p>
        </div>
      )}

      {hasSearched && !loading && results.length === 0 && (
        <div className="search-empty">
          <h3>No matches</h3>
          <p>No saved words contain "{searchedQuery}".</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="search-results">
          <div className="search-summary">
            <span>{results.length} match{results.length === 1 ? '' : 'es'}</span>
            <span>Query: {searchedQuery}</span>
          </div>

          {results.map((word) => (
            <article key={word.id} className="word-result">
              <div className="word-result-main">
                <div>
                  <h3>{word.german_word}</h3>
                  <p>{word.meaning || 'No meaning added yet.'}</p>
                </div>
                <div className="word-result-meta">
                  <span className={`status-chip ${getStatusClass(word.enrichment_status)}`}>
                    {word.enrichment_status}
                  </span>
                  <span className="examples-chip">
                    {word.example_count} example{word.example_count === 1 ? '' : 's'}
                  </span>
                </div>
              </div>

              <div className="word-result-details">
                {word.notes && <span className="tag">{word.notes}</span>}
                <span>Added {formatCreatedAt(word.created_at)}</span>
              </div>

              <div className="word-result-actions">
                <button
                  type="button"
                  className="close-btn"
                  disabled={!word.has_examples}
                  onClick={() => setExpandedWordId((activeId) => activeId === word.id ? null : word.id)}
                >
                  {expandedWordId === word.id ? 'Hide Examples' : 'View Examples'}
                </button>
              </div>

              {expandedWordId === word.id && <ExamplesPanel wordId={word.id} />}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
