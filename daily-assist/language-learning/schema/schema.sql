CREATE TABLE words (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    german_word       TEXT NOT NULL UNIQUE,
    meaning           TEXT,                      -- nullable now: GPT can fill this too
    notes             TEXT,
    enrichment_status TEXT NOT NULL DEFAULT 'pending',
                                                 -- pending | processing | completed | failed
    enrichment_attempts INT DEFAULT 0,           -- for retry logic
    last_error        TEXT,                      -- store failure reason
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_words_status ON words(enrichment_status);  -- fast queue polling

CREATE TABLE prompts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    template    TEXT NOT NULL,   -- e.g. "Give me 3 example sentences for the German word '{{word}}' ..."
    is_default  BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX uq_prompts_single_default
ON prompts (is_default)
WHERE is_default = TRUE;

CREATE TABLE enrichment_jobs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word_id       UUID NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    prompt_id     UUID REFERENCES prompts(id),
    status        TEXT NOT NULL,              -- pending | processing | completed | failed
    raw_response  TEXT,                       -- full GPT JSON response, for debugging
    error_message TEXT,
    started_at    TIMESTAMPTZ,
    completed_at  TIMESTAMPTZ,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE example_sentences (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word_id       UUID NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    sentence_de   TEXT NOT NULL,
    sentence_en   TEXT,
    source        TEXT DEFAULT 'gpt',         -- 'gpt' | 'manual' | 'imported'
    prompt_id     UUID REFERENCES prompts(id),-- which prompt generated this
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE flashcard_views (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word_id      UUID NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    viewed_at    TIMESTAMPTZ DEFAULT NOW(),
    confidence   SMALLINT CHECK (confidence BETWEEN 1 AND 5)  -- optional: 1=hard, 5=easy
);
