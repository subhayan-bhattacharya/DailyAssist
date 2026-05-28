#!/bin/bash
set -e

echo "Fetching shared frontend infrastructure outputs..."
cd ../shared-infra/frontend
S3_BUCKET=$(terraform output -raw s3_bucket_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
COGNITO_USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)
COGNITO_CLIENT_ID=$(terraform output -raw cognito_client_id)
WEBSITE_URL=$(terraform output -raw website_url)
cd - > /dev/null

echo "Fetching Reminders API output..."
cd ../reminders/terraform/lambda
REMINDERS_API_URL=$(terraform output -raw api_gateway_url)
cd - > /dev/null

echo "Fetching Flashcards API output..."
cd ../language-learning/terraform/api
FLASHCARDS_API_URL=$(terraform output -raw api_gateway_url)
cd - > /dev/null

echo "Building unified DailyAssist shell..."
export VITE_COGNITO_USER_POOL_ID="${COGNITO_USER_POOL_ID}"
export VITE_COGNITO_CLIENT_ID="${COGNITO_CLIENT_ID}"
export VITE_REMINDERS_API_URL="${REMINDERS_API_URL}"
export VITE_FLASHCARDS_API_URL="${FLASHCARDS_API_URL}"

npm install
npm run build

echo "Syncing to S3 bucket: $S3_BUCKET"
aws s3 sync dist/ s3://${S3_BUCKET}/ --delete

echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_ID} --paths '/*'

echo "Deployment complete: $WEBSITE_URL"
