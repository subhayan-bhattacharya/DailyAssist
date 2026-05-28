# DailyAssist

DailyAssist is a small suite of personal applications behind one authenticated frontend at `https://poulomi-subhayan.click`. A shared React shell owns Cognito login, sign-out, top-level routing, and the app selector; Reminders and German Flashcards stay as separate feature modules and backend APIs.

## Architecture Overview

```
React shell (Amplify auth)
  -> /reminders  -> Reminders feature -> API Gateway (Cognito authorizer) -> Lambda -> FastAPI -> DynamoDB -> SNS
  -> /flashcards -> Flashcards feature -> API Gateway (Cognito authorizer) -> Lambda -> FastAPI -> Postgres
```

## AWS Services

| Service | Purpose |
|---------|---------|
| **S3** | Hosts the unified React shell static assets (JS bundles, CSS, index.html) |
| **CloudFront** | CDN — serves the apex domain, terminates SSL, and falls back to `index.html` for SPA routes |
| **Route53** | DNS — maps `poulomi-subhayan.click` to the CloudFront distribution |
| **ACM** | SSL/TLS certificate for the custom domain |
| **Cognito** | User pool and app client for authentication |
| **API Gateway** | REST APIs with Cognito authorizers |
| **Lambda** | Runs each FastAPI backend via Mangum ASGI adapter |
| **DynamoDB** | Stores reminders (hash: `reminder_id`, range: `user_id`) |
| **Postgres** | Stores German Flashcards vocabulary, prompts, settings, and review data |
| **SNS** | Sends reminder notifications |

## Frontend Deployment

The production frontend is built from `frontend-shell/` and deployed to the apex-domain infrastructure in `shared-infra/frontend/`.

### Request Flow

```
Browser hits https://poulomi-subhayan.click
      |
      v
 1. Route53 (DNS)
    A-record alias -> resolves to CloudFront distribution IPs
      |
      v
 2. CloudFront (CDN + SSL termination)
    - TLS 1.2+ handshake using ACM cert (provisioned in us-east-1, required by CloudFront)
    - Checks edge cache; on miss, fetches from S3 origin via OAC (SigV4 signed)
    - Custom error responses: 403/404 -> returns /index.html with HTTP 200 (SPA routing)
      |
      v
 3. S3 Bucket ("poulomi-subhayan.click")
    - All public access BLOCKED
    - Only CloudFront can read objects (bucket policy scoped to distribution ARN)
    - Serves index.html + Vite-built JS/CSS bundles
      |
   [React shell loads in browser, Amplify initializes]
      |
      v
 4. Cognito (Authentication)
    - Amplify UI <Authenticator> component renders login form
    - User credentials sent directly to Cognito (SRP auth)
    - Cognito returns ID token, access token, refresh token (1hr / 1hr / 30d)
    - Tokens stored in browser storage
      |
   [User is now authenticated]
      |
      v
 5. API calls to backends
    - Feature API clients call their API Gateway endpoint with the Cognito ID token in the Authorization header
    - API Gateway validates token via its Cognito authorizer
    - Reminders requests resolve `cognito:username` and use it as the DynamoDB `user_id`
    - Flashcards requests are authenticated before reaching the language-learning FastAPI app
    - CORS headers allow origin: https://poulomi-subhayan.click
```

### S3 + CloudFront Security

The S3 bucket is completely private with all public access blocked. CloudFront uses **Origin Access Control (OAC)** with SigV4 signing — the modern replacement for the deprecated OAI. The bucket policy only allows `s3:GetObject` from the specific CloudFront distribution ARN, so objects cannot be accessed directly via S3 URLs.

### SPA Routing

CloudFront has custom error responses that return `/index.html` with HTTP 200 for both 403 and 404 errors (10s cache TTL). This enables React Router client-side navigation — any path like `/reminders/123` still receives `index.html`, and React handles the routing in the browser.

### ACM Certificate

The SSL certificate is created in `us-east-1` (a CloudFront requirement) with DNS validation. Terraform automatically creates the Route53 validation records and uses a `create_before_destroy` lifecycle for zero-downtime certificate rotation.

### Cognito App Client

Configured with `generate_secret = false` (required for browser-based apps). Supports SRP, password, and refresh token auth flows. `prevent_user_existence_errors` is enabled to block account enumeration attacks. Readable/writable attributes: email, name, preferred_username.

### Deployment Process

Deploy the frontend with `frontend-shell/deploy.sh`. The script reads Terraform outputs from `shared-infra/frontend`, `reminders/terraform/lambda`, and `language-learning/terraform/api`, then builds and syncs the unified shell to the apex S3 bucket.

## Development Commands

### Backend (Python — uses `uv` package manager)

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
cd frontend-shell
npm run dev      # Dev server on port 5173
npm run build    # TypeScript compile + Vite build
npm run lint     # ESLint
```

### Infrastructure (Terraform)

```bash
# Deploy Lambda + API Gateway
cd reminders/terraform/lambda
terraform init && terraform apply

# Deploy frontend infrastructure (S3 + CloudFront + Route53 + ACM)
cd shared-infra/frontend
terraform init && terraform apply
```

## Key Code Layout (under `reminders/`)

- `app.py` — FastAPI app, Mangum handler, route definitions, user context dependency
- `core/utils.py` — Business logic for all CRUD operations
- `core/data_structures.py` — Pydantic models for API requests/responses
- `core/backend/dynamodb/dynamo_backend.py` — `DynamoBackend` static class wrapping all DynamoDB operations
- `core/backend/dynamodb/models.py` — PynamoDB model for the Reminders table
- `core/lambda_handlers.py` — Scheduled Lambda logic (query/send reminders, delete expired)
- `core/reminder_frequency.py` — `next_reminder_date_time` calculation based on frequency
- `core/datetime_utils.py` — DateTime parsing/formatting helpers
- `frontend/` — React + TypeScript + Vite application
- `terraform/frontend/` — Frontend infrastructure (S3, CloudFront, Route53, ACM, Cognito app client)
- `terraform/lambda/` — Backend infrastructure (Lambda, API Gateway, CORS)
