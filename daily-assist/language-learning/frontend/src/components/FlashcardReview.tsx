import { useEffect, useMemo, useState } from 'react';
import { deleteWord, fetchFlashcards, recordFlashcardView } from '../api/client';
import type { FlashcardWord } from '../api/types';
import { ExamplesPanel } from './ExamplesPanel';

const confidenceOptions = [
  { value: 1, label: 'Hard' },
  { value: 2, label: 'Struggle' },
  { value: 3, label: 'OK' },
  { value: 4, label: 'Good' },
  { value: 5, label: 'Easy' },
];

function getWordId(word: FlashcardWord): string {
  return word.id ?? word.word_id ?? '';
}

function formatReviewDate(value: string): string {
  return new Date(`${value}T00:00:00`).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
}

function getTextSizeClass(value: string): string {
  const length = value.length;

  if (length > 42) return 'text-fit-xs';
  if (length > 30) return 'text-fit-sm';
  if (length > 20) return 'text-fit-md';

  return '';
}

export function FlashcardReview() {
  const [date, setDate] = useState('');
  const [words, setWords] = useState<FlashcardWord[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [examplesOpen, setExamplesOpen] = useState(false);
  const [scores, setScores] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completed, setCompleted] = useState(false);

  const currentWord = words[currentIndex];
  const wordId = currentWord ? getWordId(currentWord) : '';
  const wordSizeClass = currentWord ? getTextSizeClass(currentWord.german_word) : '';
  const meaningSizeClass = currentWord ? getTextSizeClass(currentWord.meaning ?? '') : '';
  const currentScore = wordId ? scores[wordId] : undefined;
  const reviewedCount = Object.keys(scores).length;
  const progressPercent = words.length > 0 ? ((currentIndex + 1) / words.length) * 100 : 0;
  const progressText = useMemo(() => (
    words.length === 0 ? 'No cards' : `Card ${Math.min(currentIndex + 1, words.length)} of ${words.length}`
  ), [currentIndex, words.length]);

  async function loadFlashcards() {
    try {
      setLoading(true);
      setError(null);
      setCompleted(false);
      setCurrentIndex(0);
      setRevealed(false);
      setExamplesOpen(false);
      setScores({});
      const data = await fetchFlashcards();
      setDate(data.date);
      setWords(data.words);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load flashcards.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadFlashcards();
  }, []);

  async function submitConfidence(confidence: number) {
    if (!wordId) return;
    try {
      setSubmitting(true);
      setError(null);
      await recordFlashcardView(wordId, confidence);
      setScores((existingScores) => ({ ...existingScores, [wordId]: confidence }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not save confidence.');
    } finally {
      setSubmitting(false);
    }
  }

  async function deleteCurrentWord() {
    if (!wordId || !currentWord) return;

    const confirmed = window.confirm(`Delete "${currentWord.german_word}" from your vocabulary?`);
    if (!confirmed) return;

    try {
      setDeleting(true);
      setError(null);
      await deleteWord(wordId);

      const data = await fetchFlashcards();
      const nextIndex = data.words.length === 0 ? 0 : Math.min(currentIndex, data.words.length - 1);
      const nextWordIds = new Set(data.words.map((word) => getWordId(word)));

      setDate(data.date);
      setWords(data.words);
      setCurrentIndex(nextIndex);
      setRevealed(false);
      setExamplesOpen(false);
      setCompleted(false);
      setScores((existingScores) => {
        const updatedScores: Record<string, number> = {};
        for (const [scoreWordId, score] of Object.entries(existingScores)) {
          if (scoreWordId !== wordId && nextWordIds.has(scoreWordId)) {
            updatedScores[scoreWordId] = score;
          }
        }
        return updatedScores;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete the word.');
    } finally {
      setDeleting(false);
    }
  }

  if (loading) return <div className="loading">Loading today's flashcards...</div>;

  if (error && words.length === 0) {
    return <div className="error"><p>Error: {error}</p><button type="button" onClick={loadFlashcards}>Retry</button></div>;
  }

  if (words.length === 0) {
    return <div className="empty-state"><h2>No cards for today</h2><p>Add new vocabulary or check that enriched words exist in the database.</p></div>;
  }

  if (completed) {
    return (
      <section className="completion-panel">
        <p className="eyebrow">{date ? formatReviewDate(date) : 'Today'}</p>
        <h2>Review complete</h2>
        <p>You recorded confidence for {words.length} cards.</p>
        <div className="form-actions">
          <button type="button" className="add-btn" onClick={() => { setCurrentIndex(0); setRevealed(false); setExamplesOpen(false); setCompleted(false); }}>Review Again</button>
          <button type="button" className="refresh-btn" onClick={loadFlashcards}>Refresh</button>
        </div>
      </section>
    );
  }

  function goToCard(nextIndex: number) {
    const boundedIndex = Math.min(Math.max(nextIndex, 0), words.length - 1);
    setCurrentIndex(boundedIndex);
    setRevealed(false);
    setExamplesOpen(false);
    setError(null);
  }

  function goNext() {
    if (currentIndex >= words.length - 1) {
      setCompleted(true);
      return;
    }

    goToCard(currentIndex + 1);
  }

  return (
    <section className="study-screen">
      <div className="study-toolbar">
        <div>
          <p className="eyebrow">{date ? formatReviewDate(date) : 'Today'}</p>
          <h2>Daily Review</h2>
        </div>
        <div className="study-stats" aria-label="Review progress">
          <span>{progressText}</span>
          <span>{reviewedCount} scored</span>
        </div>
      </div>

      <div className="study-progress" aria-hidden="true">
        <span style={{ width: `${progressPercent}%` }} />
      </div>

      <aside className="card-strip" aria-label="Flashcard list">
        {words.map((word, index) => {
          const stripWordId = getWordId(word);
          return (
            <button
              key={stripWordId || word.german_word}
              type="button"
              className={`strip-dot ${index === currentIndex ? 'active' : ''} ${scores[stripWordId] ? 'scored' : ''}`}
              onClick={() => goToCard(index)}
              aria-label={`Go to card ${index + 1}`}
            />
          );
        })}
      </aside>

      <div className="study-main">
        <button
          type="button"
          className={`flashcard-stage ${revealed ? 'is-revealed' : ''}`}
          onClick={() => setRevealed((value) => !value)}
          aria-label={revealed ? 'Hide meaning' : 'Reveal meaning'}
        >
          <span className="card-corner">{revealed ? 'Meaning' : 'German'}</span>
          <span className="card-count">{currentIndex + 1}/{words.length}</span>
          <span className="flashcard-front">
            <span className="word-label">Word or phrase</span>
            <strong className={wordSizeClass}>{currentWord.german_word}</strong>
            {currentWord.notes && <span className="card-note">{currentWord.notes}</span>}
          </span>
          <span className="flashcard-back">
            <span className="word-label">Meaning</span>
            <strong className={meaningSizeClass}>{currentWord.meaning || 'No meaning has been added yet.'}</strong>
            <span className="card-note">Click the card to hide this side.</span>
          </span>
        </button>

        <div className="study-actions">
          <button type="button" className="nav-btn nav-arrow" onClick={() => goToCard(currentIndex - 1)} disabled={currentIndex === 0} aria-label="Previous card">
            ←
          </button>
          <button type="button" className="add-btn reveal-btn" onClick={() => setRevealed((value) => !value)}>
            {revealed ? 'Hide Meaning' : 'Flip Card'}
          </button>
          <button type="button" className="secondary-btn" onClick={() => setExamplesOpen(true)}>
            Examples
          </button>
          <button type="button" className="danger-btn" onClick={deleteCurrentWord} disabled={deleting || submitting}>
            {deleting ? 'Deleting...' : 'Delete'}
          </button>
          <button type="button" className="nav-btn primary-next nav-arrow" onClick={goNext} aria-label={currentIndex >= words.length - 1 ? 'Finish' : 'Next card'}>
            {currentIndex >= words.length - 1 ? '✓' : '→'}
          </button>
        </div>

        <div className="confidence-dock">
          <div>
            <h3>How did this feel?</h3>
            <p>Score the card after reviewing the word.</p>
          </div>
          <div className="confidence-buttons">
            {confidenceOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                className={`confidence-btn ${currentScore === option.value ? 'selected' : ''}`}
                disabled={submitting}
                onClick={() => submitConfidence(option.value)}
              >
                <span>{option.value}</span>{option.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {examplesOpen && (
        <div className="examples-modal-backdrop" onClick={() => setExamplesOpen(false)}>
          <div className="examples-modal" onClick={(e) => e.stopPropagation()}>
            <div className="examples-modal-header">
              <h3>Examples — {currentWord.german_word}</h3>
              <button type="button" className="examples-modal-close" onClick={() => setExamplesOpen(false)}>✕</button>
            </div>
            <ExamplesPanel wordId={wordId} />
          </div>
        </div>
      )}

      {error && <p className="form-error">{error}</p>}
    </section>
  );
}
