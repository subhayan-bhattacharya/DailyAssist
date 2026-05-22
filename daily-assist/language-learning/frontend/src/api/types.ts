export interface FlashcardWord {
  id: string;
  word_id?: string;
  german_word: string;
  meaning: string | null;
  notes: string | null;
}

export interface FlashcardsResponse {
  date: string;
  words: FlashcardWord[];
}

export interface WordCreateRequest {
  german_word: string;
  meaning?: string;
  notes?: string;
}

export interface WordResponse {
  id: string;
  german_word: string;
  meaning: string | null;
  notes: string | null;
  enrichment_status: string;
  created_at: string;
}

export interface WordSearchResult extends WordResponse {
  example_count: number;
  has_examples: boolean;
}

export interface WordSearchResponse {
  query: string;
  count: number;
  words: WordSearchResult[];
}

export interface ExampleSentence {
  sentence_de: string;
  sentence_en: string;
}

export interface ExamplesResponse {
  word_id: string;
  german_word: string;
  sentences: ExampleSentence[];
}

export interface AppSettings {
  daily_word_count: number | null;
}

export interface Prompt {
  id: string;
  name: string;
  template: string;
  is_default: boolean;
  created_at: string;
}

export interface PromptCreateRequest {
  name: string;
  template: string;
}
