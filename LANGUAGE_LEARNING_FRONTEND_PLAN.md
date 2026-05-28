# Language Learning Frontend Plan

> Update 2026-05-28: the shared authenticated shell described here is now tracked in `docs/plans/2026-05-28-unified-domain-auth.md` and implemented under `daily-assist/frontend-shell`. Language Learning should remain a feature section mounted by that shell, not a standalone owner of login/header behavior.

## Goal
Build a React + TypeScript + Vite frontend for the German flashcards language-learning app, visually aligned with the existing Daily Assist reminders frontend so it can become one section of the authenticated Daily Assist site.

No implementation should start until this plan is approved.

## Source Context
- API docs: `daily-assist/language-learning/API_DOCS.md`
- Existing visual reference: `daily-assist/reminders/frontend`
- Existing backend app: `daily-assist/language-learning/api/app.py`

## Product Shape
The long-term product shape is a single authenticated Daily Assist window. After login, the user should be able to choose between the Reminders app and the Language Learning app, then move into either experience.

For this first frontend pass, focus on making the Language Learning app ready as a self-contained section that can later be mounted behind that shared authenticated app selector.

The language-learning section itself should feel like a focused daily study tool, not a broad dashboard. The primary screen should put today's flashcards first, with supporting vocabulary, examples, settings, and prompt controls available without overwhelming the daily session.

## Long-Term User Flow
1. User opens Daily Assist.
2. User signs in once using the existing Amplify/Cognito pattern.
3. Authenticated home screen shows app choices:
   - Reminders
   - German Flashcards
4. User selects German Flashcards.
5. The language-learning section opens inside the same authenticated shell.

## First-Pass User Flow
1. User signs in using the same Amplify/Cognito pattern as reminders, or the app receives an already-authenticated shell later.
2. Language Learning opens to "Daily Assist - German Flashcards".
3. Today's review cards are loaded from `GET /flashcards/`.
4. User studies one word at a time:
   - German word is shown first.
   - Meaning and notes can be revealed.
   - Examples can be fetched on demand from `GET /words/{word_id}/examples`.
   - User records confidence from 1 to 5.
5. After each confidence submission, frontend posts to `POST /flashcards/view` and advances to the next card.
6. User can add new vocabulary from a compact form.
7. User can update daily word count from settings.
8. User can view and update the default enrichment prompt from an admin-style panel.

## Navigation Model
For the language-learning section, use a simple tab row:

- `Review`: main daily flashcard session.
- `Add Word`: vocabulary creation form.
- `Settings`: daily word count.
- `Prompt`: enrichment prompt editor.

This keeps the section single-page and consistent with the reminders frontend's compact layout.

Later, the parent Daily Assist shell should provide the top-level app chooser. The language-learning section should not hard-code assumptions that prevent it from being mounted under something like `/language-learning`.

## Overall Layout
Reuse the reminders structure:

- `main.app-container`: max width around `800px`, centered, `20px` padding.
- `header.app-header`: indigo gradient, white title, signed-in user, sign out button.
- Main content surface: white panel with `8px` radius and subtle shadow.
- Detail/highlight panels: light indigo background `#e8eaf6`, border `#c5cae9`.
- Primary actions: indigo `#1a237e`, hover `#283593`.
- Secondary positive action: green `#4CAF50`, hover `#45a049`.
- Error: `#d32f2f`.
- Tags/badges: light blue `#e3f2fd`, text `#1565c0`, border `#bbdefb`.

## Screen Design

### 1. App Header
Title: `Daily Assist - German Flashcards`

Right side:
- `Welcome, {loginId}`
- `Sign Out`

Implementation should mirror `reminders/frontend/src/App.tsx` for the first pass. When the shared Daily Assist shell is built, this can be lifted up so Language Learning receives user/session controls from the parent.

### 2. Review Screen
Primary content:
- Date label from `GET /flashcards/`.
- Progress indicator: `Card 3 of 10`.
- Flashcard panel:
  - German word as the main heading.
  - Meaning hidden behind a `Reveal` button initially.
  - Notes shown as a small badge or muted line when present.
  - Examples section collapsed until requested.

Actions:
- `Reveal`
- `Examples`
- Confidence buttons:
  - `1 Hard`
  - `2 Struggling`
  - `3 OK`
  - `4 Good`
  - `5 Easy`

Behavior:
- Disable confidence buttons until the card is revealed.
- Posting confidence calls `POST /flashcards/view`.
- On success, mark the local card completed and move forward.
- At the end, show a compact completion state with review count and a `Review Again` local reset.

Empty state:
- If no words are returned, show a calm empty message and a shortcut to `Add Word`.

### 3. Examples Panel
Fetch examples only when the user clicks `Examples`.

Display:
- German sentence
- English translation beneath it
- Use list rows with subtle borders, not oversized cards.

States:
- Loading: `Loading examples...`
- 404: `No examples are available for this word yet.`
- General API failure: retry button.

### 4. Add Word Screen
Fields:
- German word, required.
- Meaning, optional.
- Notes, optional.

Submit:
- `POST /words/`

Success state:
- Show created word and `enrichment_status`.
- Explain in one short line that examples will appear after enrichment if status is `pending`.

Errors:
- `409`: word already exists.
- Generic API errors shown in the same form-error style as reminders.

### 5. Settings Screen
Fetch:
- `GET /settings/`

Field:
- `daily_word_count`, positive integer.

Submit:
- `PATCH /settings/`

Important copy:
- Changes take effect the next calendar day because today's list is cached.

### 6. Prompt Screen
Fetch:
- `GET /prompts/default`

Fields:
- Prompt name.
- Prompt template textarea.

Submit:
- `POST /prompts/default`

Validation:
- Frontend should prevent submission if template does not include `{{word}}`.

404 state:
- If no prompt exists, show empty fields and allow creating the first default prompt.

## API Client Design
Create a small typed API layer instead of scattering fetch calls through components.

Suggested files:

```text
daily-assist/language-learning/frontend/src/
├── api/client.ts
├── api/types.ts
├── components/
│   ├── AddWordForm.tsx
│   ├── ExamplesPanel.tsx
│   ├── FlashcardReview.tsx
│   ├── LanguageLearningApp.tsx
│   ├── PromptEditor.tsx
│   ├── SettingsPanel.tsx
│   └── TabNav.tsx
├── utils/auth.ts
├── App.tsx
├── App.css
├── index.css
└── main.tsx
```

The reminders app currently sends the Cognito token as the `Authorization` header. The language-learning frontend should use the same helper pattern unless the backend is intentionally public.

To prepare for the future shared shell, keep `LanguageLearningApp.tsx` focused on the feature UI and keep authentication/app-shell concerns isolated in `App.tsx`.

## Environment Variables
Use:

```text
VITE_API_URL=http://127.0.0.1:8000
```

If hosted under the same site later, deployment can point this at the language-learning API Gateway URL.

## Backend/API Assumptions To Confirm
- Auth: API docs do not mention auth, but the final site should be single-authenticated. I will build frontend auth consistently with reminders for now, while keeping the feature UI separable for the later shared shell.
- CORS: backend currently allows all origins, so local Vite should work.
- Route slashes: docs show `/flashcards/`, `/words/`, and `/settings/`; the frontend should include trailing slashes for collection endpoints.
- Flashcard word ID: API docs show `id`, and backend schema aliases `word_id` to `id`; frontend should accept `id` from the wire.

## Implementation Plan After Approval
1. Scaffold `daily-assist/language-learning/frontend` as a Vite React TypeScript app, matching reminders dependency choices where practical.
2. Copy/adapt Amplify setup and auth helper from reminders.
3. Structure the code so `App.tsx` owns temporary auth/app shell behavior and `LanguageLearningApp.tsx` owns the feature UI.
4. Add typed API client and response/request types.
5. Build language-learning tab navigation.
6. Build review flow, including reveal, examples, confidence submit, progress, loading, empty, and completion states.
7. Build add-word form with duplicate handling.
8. Build settings panel with next-day note.
9. Build prompt editor with `{{word}}` validation.
10. Port and adapt CSS from reminders, keeping the same color palette and spacing.
11. Run `npm run build` and `npm run lint` if configured.
12. Start local dev server and provide the URL for review.

## Open Questions
1. For this first pass, should the frontend live at `daily-assist/language-learning/frontend` as planned?
2. Should the prompt editor be visible in the main UI, or treated as an admin-only screen later?
3. Do you want examples visible on every card by default, or fetched only when requested?
