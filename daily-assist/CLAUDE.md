# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DailyAssist is a serverless reminders application with a FastAPI backend deployed to AWS Lambda and a React frontend. Users authenticate via AWS Cognito to create, manage, and share reminders stored in DynamoDB.

## Development Commands

### Backend (Python - uses `uv` package manager)

```bash
# Start local dev environment (DynamoDB Local + FastAPI on port 8001)
docker-compose up

# Run tests (requires Docker for testcontainers DynamoDB)
cd reminders && uv run pytest

# Run a single test file
cd reminders && uv run pytest tests/unit/test_datastructures.py

# Run a single test
cd reminders && uv run pytest tests/app/test_app.py::test_function_name -v
```

### Frontend (React + TypeScript + Vite)

```bash
cd reminders/frontend
npm run dev      # Dev server on port 5173
npm run build    # TypeScript compile + Vite build
npm run lint     # ESLint
```

### Infrastructure (Terraform)

```bash
# Deploy Lambda + API Gateway
cd reminders/terraform/lambda
terraform init && terraform apply
```

## Architecture

```
React (Amplify auth) → API Gateway (Cognito authorizer) → Lambda (Mangum) → FastAPI → DynamoDB
                                                                                    → SNS (notifications)
```

**Request flow:** Frontend fetches Cognito ID token via Amplify, sends it in the Authorization header. API Gateway validates the token. Lambda receives the event and Mangum adapts it to ASGI for FastAPI. The `get_user_context` dependency in `app.py` extracts user identity from `request.scope["aws.event"]` claims. In local dev (`ENVIRONMENT=local`), a mock user is returned instead.

**Scheduled Lambda functions** (`lambda_query_and_send_reminders_handler`, `lambda_delete_expired_reminders_handler`) run independently of the API to send due reminders via SNS and clean up expired entries.

## Key Code Layout (under `reminders/`)

- `app.py` — FastAPI app, Mangum handler, route definitions, user context dependency
- `core/utils.py` — Business logic for all CRUD operations (called by route handlers)
- `core/data_structures.py` — Pydantic models for API requests/responses
- `core/backend/dynamodb/dynamo_backend.py` — `DynamoBackend` static class wrapping all DynamoDB operations
- `core/backend/dynamodb/models.py` — PynamoDB model for the Reminders table
- `core/lambda_handlers.py` — Scheduled Lambda logic (query/send reminders, delete expired)
- `core/reminder_frequency.py` — `next_reminder_date_time` calculation based on frequency
- `core/datetime_utils.py` — DateTime parsing/formatting helpers
- `tests/conftest.py` — Pytest fixtures: spins up DynamoDB Local via testcontainers, creates table with GSI

## Important Patterns

- **DynamoDB key schema:** `reminder_id` (hash) + `user_id` (range). GSI `UserIdReminderTitleGsi2` on `user_id` (hash) + `reminder_title` (range) for efficient per-user queries.
- **Sharing:** Duplicates the reminder record with a different `user_id` (same `reminder_id`, new range key).
- **Duplicate prevention:** Before creating a reminder, queries the GSI to check if the user already has one with the same title.
- **Tests use real DynamoDB Local** via testcontainers (Docker required). The `reminders` fixture creates and tears down the table per test. The `reminders_model` fixture points PynamoDB to the local endpoint.
- **Python version:** 3.13 (see `.python-version`).
- **AWS region:** eu-central-1 throughout.
