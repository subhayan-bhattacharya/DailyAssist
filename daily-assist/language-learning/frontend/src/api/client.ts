import { getAuthToken } from '../utils/auth';
import type {
  AppSettings,
  ExamplesResponse,
  FlashcardsResponse,
  Prompt,
  PromptCreateRequest,
  WordDeleteResponse,
  WordCreateRequest,
  WordResponse,
  WordSearchResponse,
} from './types';

const apiUrl = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';
const useMockApi = import.meta.env.VITE_MOCK_API === 'true';

const mockWords: FlashcardsResponse = {
  date: new Date().toISOString().slice(0, 10),
  words: [
    {
      id: 'mock-1',
      german_word: 'die Geselligkeit',
      meaning: 'sociability, conviviality',
      notes: 'noun',
    },
    {
      id: 'mock-2',
      german_word: 'sich ausruhen',
      meaning: 'to rest',
      notes: 'reflexive verb',
    },
    {
      id: 'mock-3',
      german_word: 'außergewöhnlich',
      meaning: 'exceptional, extraordinary',
      notes: 'adjective',
    },
  ],
};

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getAuthToken();
  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');

  if (token) {
    headers.set('Authorization', token);
  }

  const response = await fetch(`${apiUrl}${path}`, { ...options, headers });

  if (!response.ok) {
    const text = await response.text();
    throw new ApiError(text || `Request failed with status ${response.status}`, response.status);
  }

  return response.json() as Promise<T>;
}

export function getApiBaseUrl(): string {
  return apiUrl;
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function fetchFlashcards(): Promise<FlashcardsResponse> {
  if (useMockApi) {
    return Promise.resolve(mockWords);
  }

  return request<FlashcardsResponse>('/flashcards/');
}

export function recordFlashcardView(wordId: string, confidence: number): Promise<{ word_id: string; viewed_at: string }> {
  if (useMockApi) {
    return Promise.resolve({ word_id: wordId, viewed_at: new Date().toISOString() });
  }

  return request('/flashcards/view', {
    method: 'POST',
    body: JSON.stringify({ word_id: wordId, confidence }),
  });
}

export function createWord(payload: WordCreateRequest): Promise<WordResponse> {
  return request<WordResponse>('/words/', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function searchWords(query: string, limit = 20): Promise<WordSearchResponse> {
  if (useMockApi) {
    const normalizedQuery = query.trim().toLowerCase();
    const words = mockWords.words
      .filter((word) => word.german_word.toLowerCase().includes(normalizedQuery))
      .map((word, index) => ({
        id: word.id,
        german_word: word.german_word,
        meaning: word.meaning,
        notes: word.notes,
        enrichment_status: index === 1 ? 'pending' : 'completed',
        created_at: new Date().toISOString(),
        example_count: index === 1 ? 0 : 2,
        has_examples: index !== 1,
      }))
      .slice(0, limit);

    return Promise.resolve({
      query,
      count: words.length,
      words,
    });
  }

  const params = new URLSearchParams({
    q: query,
    limit: String(limit),
  });

  return request<WordSearchResponse>(`/words/search?${params.toString()}`);
}

export function deleteWord(wordId: string): Promise<WordDeleteResponse> {
  if (useMockApi) {
    const word = mockWords.words.find((item) => item.id === wordId);
    return Promise.resolve({
      id: wordId,
      german_word: word?.german_word ?? 'Deleted word',
      message: 'Word successfully deleted',
    });
  }

  return request<WordDeleteResponse>(`/words/${wordId}`, {
    method: 'DELETE',
  });
}

export function fetchExamples(wordId: string): Promise<ExamplesResponse> {
  if (useMockApi) {
    const word = mockWords.words.find((item) => item.id === wordId) ?? mockWords.words[0];
    return Promise.resolve({
      word_id: word.id,
      german_word: word.german_word,
      sentences: [
        {
          sentence_de: `Ich habe ${word.german_word} in einem langen Gespräch besser verstanden.`,
          sentence_en: `I understood ${word.german_word} better in a long conversation.`,
        },
        {
          sentence_de: `Wir haben über ${word.german_word} gesprochen, weil das Thema wichtig gewesen ist.`,
          sentence_en: `We talked about ${word.german_word} because the topic was important.`,
        },
      ],
    });
  }

  return request<ExamplesResponse>(`/words/${wordId}/examples`);
}

export function fetchSettings(): Promise<AppSettings> {
  return request<AppSettings>('/settings/');
}

export function updateSettings(payload: AppSettings): Promise<AppSettings> {
  return request<AppSettings>('/settings/', {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export function fetchDefaultPrompt(): Promise<Prompt> {
  return request<Prompt>('/prompts/default');
}

export function createDefaultPrompt(payload: PromptCreateRequest): Promise<Prompt> {
  return request<Prompt>('/prompts/default', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
