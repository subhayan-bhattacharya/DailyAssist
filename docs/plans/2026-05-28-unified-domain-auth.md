---
title: Unified Domain Auth Migration
type: feat
status: active
date: 2026-05-28
---

# Unified Domain Auth Migration

## Goal

Move DailyAssist from `reminders.poulomi-subhayan.click` and `flashcards.poulomi-subhayan.click` to a single authenticated entry point at `poulomi-subhayan.click`. Users sign in once, land on an app selector, and navigate to Reminders or German Flashcards while preserving the Cognito identity Reminders already uses for per-user data.

## Approach

Create a shared React shell that owns Amplify configuration, login, app routing, the app selector, sign-out, and generic authenticated HTTP helpers. Reminders and Flashcards remain feature modules mounted under shell routes, while their domain-specific UI and API functions stay local to each app.

## Key Decisions

- Preserve Reminders' canonical user key as Cognito `cognito:username`; changing it would require a DynamoDB and scheduled-notification migration.
- Use the existing apex CloudFront/S3 stack under `daily-assist/shared-infra/frontend` as the long-term frontend host.
- Secure Flashcards at the API layer as part of the migration because its frontend can send tokens today but API Gateway currently allows unauthenticated calls.
- Defer full Flashcards per-user Postgres partitioning; current Flashcards data is global and that migration is larger than the domain/login cutover.

## Implementation Units

- U1. Create `daily-assist/frontend-shell` with shared Amplify setup, login, header, selector, routing, and auth-aware HTTP helpers.
- U2. Refactor Reminders frontend calls into `daily-assist/reminders/frontend/src/api/*` and mount `RemindersList` from the shell at `/reminders`.
- U3. Refactor Flashcards so `LanguageLearningApp` is the feature root mounted by the shell at `/flashcards`, with duplicate login/header code removed from feature behavior.
- U4. Extract a shared FastAPI user-context dependency and reuse it from Reminders and Language Learning APIs.
- U5. Add a Cognito authorizer to the Language Learning API Gateway and align CORS defaults to `https://poulomi-subhayan.click`.
- U6. Replace per-app frontend deploys with an apex-domain shell deploy, keeping subdomain redirect/decommission work explicit.
- U7. Add focused tests and docs covering route loading, token propagation, backend identity extraction, CORS/auth expectations, and deployment layout.

## Files Affected

- `daily-assist/frontend-shell/**`
- `daily-assist/reminders/frontend/src/App.tsx`
- `daily-assist/reminders/frontend/src/components/*`
- `daily-assist/reminders/frontend/src/api/*`
- `daily-assist/language-learning/frontend/src/App.tsx`
- `daily-assist/language-learning/frontend/src/api/client.ts`
- `daily-assist/shared/python/auth.py`
- `daily-assist/reminders/app.py`
- `daily-assist/language-learning/api/app.py`
- `daily-assist/language-learning/api/routes/*`
- `daily-assist/language-learning/terraform/api/*`
- `daily-assist/reminders/terraform/lambda/variables.tf`
- `daily-assist/shared-infra/frontend/*`
- `daily-assist/README.md`

## Verification

- `poulomi-subhayan.click` shows one login screen and then an app selector.
- `/reminders` and `/flashcards` deep links load after authentication and refresh.
- Reminders API requests still carry the Cognito token and resolve the same user identity.
- Flashcards API rejects unauthenticated production requests once API Gateway auth is enabled.
- CORS preflight succeeds from the apex domain for both APIs.
- Existing Reminders backend tests continue to pass, and new Language Learning auth tests cover protected routes.

