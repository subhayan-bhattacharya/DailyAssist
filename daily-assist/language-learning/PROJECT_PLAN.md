# Language Learning App — Backend Plan

## Context
Build the Python backend for a German flashcard app. The database schema (5 tables) and Neon Postgres infrastructure already exist. The goal is to add a FastAPI REST API (deployed as an AWS Lambda), a nightly OpenAI enrichment cron job (separate Lambda), and the daily word-selection logic that surfaces 10 words per day as flashcards.

---

## Schema Changes: Two New Tables

### 1. `daily_selections` — caches today's word set
```sql
CREATE TABLE daily_selections (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    selected_on DATE NOT NULL UNIQUE,
    word_ids    UUID[] NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### 2. `app_settings` — user-configurable app settings
```sql
CREATE TABLE app_settings (
    key        TEXT PRIMARY KEY,
    value      TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default
INSERT INTO app_settings (key, value) VALUES ('daily_word_count', '10');
```

**Implementation:** Add `DailySelection` and `AppSetting` SQLAlchemy models to `db/models.py`, then generate a single Alembic migration for both tables.

---

## Project Structure

```
daily-assist/language-learning/
├── pyproject.toml                 # add fastapi, mangum, pydantic, openai, python-dotenv
├── db/
│   ├── __init__.py                # NEW
│   └── models.py                  # MODIFIED: add DailySelection model
├── migrations/versions/
│   └── <rev>_add_daily_selections.py  # NEW migration
├── core/
│   ├── __init__.py
│   ├── database.py                # SQLAlchemy engine (NullPool) + session context manager
│   ├── flashcard_service.py       # daily word selection logic
│   ├── word_service.py            # add word logic
│   ├── example_service.py        # fetch examples for a word
│   └── settings_service.py       # get/update app_settings
├── api/
│   ├── __init__.py
│   ├── app.py                     # FastAPI app + CORS + Mangum handler
│   ├── schemas.py                 # Pydantic request/response models
│   └── routes/
│       ├── flashcards.py          # GET /flashcards, POST /flashcards/view
│       ├── words.py               # POST /words
│       ├── examples.py            # GET /words/{word_id}/examples
│       └── settings.py            # GET /settings, PATCH /settings
├── cron/
│   ├── __init__.py
│   └── enrichment_handler.py     # nightly Lambda handler (no FastAPI)
├── Dockerfile                     # Lambda container image (CMD: api.app.handler)
├── Dockerfile.dev                 # local uvicorn dev image
├── docker-compose.yml             # local Postgres + API
└── terraform/
    ├── (existing neon/ — unchanged)
    ├── api_lambda/main.tf         # ECR + Lambda + API Gateway
    └── cron_lambda/main.tf        # EventBridge + cron Lambda (ZIP packaged)
```

---

## API Endpoints

### GET /flashcards
Returns today's 10 words (no sentences — those are on-demand).
```json
{
  "date": "2026-05-18",
  "words": [
    { "word_id": "uuid", "german_word": "Schlüssel", "meaning": "key", "notes": null }
  ]
}
```

### POST /flashcards/view
Records a card view with confidence score.
- Body: `{ "word_id": "uuid", "confidence": 4 }`
- Response 201: `{ "word_id": "uuid", "viewed_at": "..." }`

### GET /words/{word_id}/examples
On-demand fetch of example sentences.
```json
{
  "word_id": "uuid",
  "german_word": "Schlüssel",
  "sentences": [{ "sentence_de": "...", "sentence_en": "..." }]
}
```

### POST /words
Add a new word to be enriched tonight.
- Body: `{ "german_word": "Heimweh", "meaning": "homesickness", "notes": null }`
- Response 201: `{ "word_id": "uuid", "german_word": "Heimweh", "enrichment_status": "pending" }`
- Response 409 on duplicate.

### GET /settings
Returns all configurable app settings.
```json
{ "daily_word_count": 10 }
```

### PATCH /settings
Updates one or more settings. Changing `daily_word_count` takes effect the **next day** (today's selection is already cached in `daily_selections`).
- Body: `{ "daily_word_count": 15 }`
- Response 200: `{ "daily_word_count": 15 }`
- Response 422 if value is not a positive integer.

---

## Daily Word Selection Logic (`core/flashcard_service.py`)

1. Read `daily_word_count` from `app_settings` (default 10 if missing).
2. Check `daily_selections` for `selected_on = today`.
3. If missing: run selection query with `LIMIT daily_word_count`, `INSERT ... ON CONFLICT (selected_on) DO NOTHING`, return words.
4. If found: fetch `Word` rows for the stored `word_ids`.

**Note:** Changing `daily_word_count` via `PATCH /settings` takes effect the next calendar day, since today's selection is already cached. If you want it to take effect immediately, delete today's row from `daily_selections` (not exposed via API — a deliberate choice to prevent accidental reshuffling mid-session).

**Selection algorithm — confidence-weighted spaced repetition:**

Each confidence score maps to a review interval (days before the word should resurface):

| Confidence | Meaning | Interval |
|---|---|---|
| NULL (never seen) | — | 0 days (always prioritized) |
| 1 | Hard | 1 day |
| 2 | Struggling | 2 days |
| 3 | OK | 4 days |
| 4 | Good | 7 days |
| 5 | Easy | 14 days |

The query computes a `next_review_date` per word from its most recent view + the interval for that view's confidence. Words where `next_review_date <= today` are **due** and selected first (ordered by most overdue). Words that are not yet due are selected last as fill-in if fewer than 10 due words exist.

```sql
WITH latest_view AS (
    SELECT DISTINCT ON (word_id)
        word_id,
        viewed_at,
        confidence
    FROM flashcard_views
    ORDER BY word_id, viewed_at DESC
),
word_schedule AS (
    SELECT
        w.id,
        lv.viewed_at,
        lv.confidence,
        CASE lv.confidence
            WHEN 1 THEN lv.viewed_at + INTERVAL '1 day'
            WHEN 2 THEN lv.viewed_at + INTERVAL '2 days'
            WHEN 3 THEN lv.viewed_at + INTERVAL '4 days'
            WHEN 4 THEN lv.viewed_at + INTERVAL '7 days'
            WHEN 5 THEN lv.viewed_at + INTERVAL '14 days'
            ELSE NULL  -- never seen
        END AS next_review_at
    FROM words w
    LEFT JOIN latest_view lv ON lv.word_id = w.id
    WHERE w.enrichment_status = 'completed'
)
SELECT id FROM word_schedule
ORDER BY
    next_review_at ASC NULLS FIRST,   -- never seen & most overdue first
    viewed_at ASC NULLS FIRST          -- tie-break: least recently seen
LIMIT :daily_word_count;  -- value read from app_settings at selection time
```

**Key behaviours:**
- Never-seen words always appear before viewed words.
- A word marked confidence=5 won't resurface for 14 days unless there are fewer than 10 due words.
- A word marked confidence=1 resurfaces the very next day.
- Uses `DISTINCT ON` to grab only the **most recent** view per word (not the average).

**Schema note:** No new columns needed — `flashcard_views.confidence` already exists (SmallInteger 1–5). The `POST /flashcards/view` endpoint is essential for this algorithm to work.

---

## Nightly Enrichment Job (`cron/enrichment_handler.py`)

Plain Lambda handler — no FastAPI, no Mangum.

**Words to process:**
```sql
SELECT id, german_word FROM words
WHERE enrichment_status IN ('pending', 'failed') AND enrichment_attempts < 3
ORDER BY created_at ASC LIMIT 50
```

**Per-word loop:**
1. Fetch default prompt (`is_default = TRUE`) from `prompts` table.
2. Replace `{{word}}` placeholder in template.
3. Mark word `processing`, increment `enrichment_attempts`, create `enrichment_jobs` row.
4. Call `openai.chat.completions.create` in JSON mode.
5. Parse response → INSERT into `example_sentences` (source=`gpt`).
6. Mark word `completed`, update `enrichment_jobs` with `raw_response`.
7. On any exception: mark word `failed`, store `last_error`.

**Prompt stored in `prompts` table (seeded by `scripts/seed_prompt.py`):**

The prompt template is stored with `is_default = TRUE`. At runtime `{{word}}` is replaced with the actual German word/phrase. The JSON response includes both `meaning` (used if `words.meaning` is NULL) and 10 example sentences.

**Full template stored in DB:**
```
You are my German tutor, your job is to help me with German words, verbs, nouns, adjectives, phrases and their meanings and grammatical structures etc. You are teaching someone who has already completed B1 so teach accordingly. Whenever I ask you to explain a word or teach me a grammatical structure always explain with examples and in those examples always use present perfect unless asked for something else. I will ask for past tense when I need it so by default try to avoid it. Remember B2 level and always present perfect unless asked otherwise. Make the sentences a bit long, lets say 10 to 15 words long and include the below grammatical structures wherever possible: Nebensätze, Relativsätze, Indirekte Fragesätze, Konjunktiv II, Vorgangspassiv Präteritum, Zustandspassiv, sich lassen, Nominalisierung, Infinitiv mit zu, reflexive and dative verbs, Partizip I & II as Adjectives, Vermutung etc. When asked about the meaning of a word, give me 10 sentences including the above grammar subjects.

The word or phrase to explain is: {{word}}

You MUST respond with valid JSON only, no other text. Use this exact format:
{"meaning": "English meaning of the word or phrase", "sentences": [{"sentence_de": "German sentence here", "sentence_en": "English translation here"}]}
The sentences array must contain exactly 10 items.
```

The `meaning` from the JSON response is written to `words.meaning` **only if `words.meaning` is currently NULL** (preserves user-provided meanings).

**EventBridge schedule:** `cron(0 23 * * ? *)` — 23:00 UTC = midnight CET.
**Lambda timeout:** 300 seconds. `LIMIT 50` words ≈ 60–100s at ~1–2s/call.

---

## Database Layer (`core/database.py`)

Use `NullPool` — Lambda invocations are short-lived; connection pools would exhaust Neon's connection limit.

```python
from sqlalchemy.pool import NullPool

def get_engine():  # initialized once per warm Lambda instance
    ...
    return create_engine(db_url, poolclass=NullPool)
```

`DATABASE_URL` environment variable (from SSM Parameter Store via Terraform).

---

## Dependencies to Add (`pyproject.toml`)

```
fastapi>=0.115.0
mangum>=0.19.0
pydantic>=2.7.0
openai>=1.30.0
python-dotenv>=1.0.0
```
Dev: `uvicorn[standard]`, `pytest`, `pytest-asyncio`, `httpx`

---

## AWS Infrastructure (Terraform)

### `terraform/api_lambda/` — mirrors `reminders/terraform/lambda/main.tf`
- ECR repo → Docker build → Lambda (`package_type = "Image"`, timeout 30s, 256MB)
- API Gateway REST API with `{proxy+}` → Lambda proxy integration
- No auth (single-user app)
- Env vars from SSM: `DATABASE_URL`

### `terraform/cron_lambda/` — mirrors `reminders/terraform/scheduled/main.tf`
- ZIP package of `cron/` + `core/` + `db/` directories
- EventBridge rule: `cron(0 23 * * ? *)`
- Lambda timeout: 300s, 256MB
- Env vars from SSM: `DATABASE_URL`, `OPENAI_API_KEY`

---

## Data Seeding (before API work)

Three focused scripts under `scripts/`, each doing one thing:

### `scripts/seed_prompt.py`
- Inserts the B2 tutor prompt into the `prompts` table with `is_default = TRUE`
- Uses `ON CONFLICT (name) DO UPDATE` so re-running is safe (updates the template if changed)
- JSON response format in the prompt includes **both** `meaning` and `sentences`
- Run first, once: `uv run python scripts/seed_prompt.py`

### `scripts/seed_words.py`
- Inserts the 10 German words/phrases below, with user-provided meanings pre-filled in `words.meaning`
- `enrichment_status = 'pending'` (sentences still come from OpenAI)
- Skips duplicates via `ON CONFLICT (german_word) DO NOTHING`
- Run: `uv run python scripts/seed_words.py`

**Initial 10 words (user-provided, with meanings):**

| german_word | meaning | notes |
|---|---|---|
| `der Hinterhalt` | ambush | noun |
| `Bist du ausgeruht?` | Are you well rested? | common phrase |
| `sich ausruhen` | to rest | reflexive verb |
| `hinterhältig` | malicious | adjective (e.g. hinterhältige Fragen) |
| `schmeicheln` | to flatter | verb, takes dative |
| `Ich fühle mich geschmeichelt` | I feel flattered | common expression |
| `Ich muss ihm schmeicheln` | I must flatter him | dative usage example |
| `außergewöhnlich` | exceptional / extraordinary | adjective |
| `die Plauderei` | the chat | noun |
| `das Geplauder` | small talk | noun |

**Note on phrases:** `german_word` stores the full phrase as-is (the column is TEXT with no length limit). The enrichment prompt handles phrases naturally since it asks for sentences using/demonstrating the given word/phrase.

**Meaning handling:** Since meanings are already provided, the enrichment script will NOT overwrite `words.meaning` if it is already set. It will only fill `meaning` for words where `meaning IS NULL`.

### `scripts/run_enrichment.py`
- Reads `DATABASE_URL` + `OPENAI_API_KEY` from `.env`
- Processes all `pending` words → OpenAI → parses `meaning` + `sentences` from JSON response
- Writes `meaning` back to `words.meaning`, inserts 10 rows into `example_sentences`
- Marks word `completed`
- Run: `uv run python scripts/run_enrichment.py`

**`.env` file** (gitignored):
```
DATABASE_URL=postgres://language_app_owner:<password>@<neon-host>/language_learning
OPENAI_API_KEY=sk-...
```
Get `DATABASE_URL` from: `cd terraform && terraform output -raw app_connection_uri`

**Order:** run `seed_words.py` first, then `run_enrichment.py`. After enrichment completes, the DB has ~60 words with example sentences ready for API development and testing.

---

## Implementation Order

1. **Dependencies + models** — update `pyproject.toml`, add `DailySelection` + `AppSetting` to `db/models.py`, generate + run migration
2. **Seed data** — write `scripts/seed_words.py` + `scripts/run_enrichment.py`, populate DB with ~60 enriched German words
3. **Database layer** — `core/database.py` with `NullPool` engine
4. **Service layer** — `core/flashcard_service.py`, `word_service.py`, `example_service.py`, `settings_service.py`
5. **API schemas** — `api/schemas.py` Pydantic models
6. **Routes + app** — `api/routes/` (flashcards, words, examples, settings), `api/app.py` with Mangum handler
7. **Local dev** — `Dockerfile.dev` + `docker-compose.yml`, test all endpoints with curl against real Neon data
8. **Cron handler** — `cron/enrichment_handler.py` (reuses enrichment logic from seed scripts)
9. **Production Dockerfile** — Lambda container image, test with Lambda RIE
10. **Terraform: API Lambda** — deploy + smoke test API Gateway URL
11. **Terraform: Cron Lambda** — deploy + manually invoke to verify first enrichment run
12. **E2E validation** — add words → trigger cron → verify flashcards + examples + settings

---

## Key Reference Files
- Existing models: `daily-assist/language-learning/db/models.py`
- Existing query pattern: `daily-assist/language-learning/schema/flashcard_query.sql`
- FastAPI + Mangum pattern: `daily-assist/reminders/app.py:175`
- Lambda Dockerfile pattern: `daily-assist/reminders/Dockerfile`
- Lambda Terraform pattern: `daily-assist/reminders/terraform/lambda/main.tf`
- Scheduled Lambda Terraform: `daily-assist/reminders/terraform/scheduled/main.tf`
