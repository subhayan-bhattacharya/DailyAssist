#!/bin/bash
set -e

echo "Fetching shared infrastructure outputs..."
cd ../../shared-infra/frontend
COGNITO_USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)
cd - > /dev/null

# Fetch outputs from the reminders infrastructure
echo "Fetching infrastructure outputs..."
cd ../terraform/frontend
S3_BUCKET=$(terraform output -raw s3_bucket_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
COGNITO_CLIENT_ID=$(terraform output -raw cognito_client_id)
WEBSITE_URL=$(terraform output -raw website_url)
cd - > /dev/null

echo "Fetching API outputs..."
cd ../terraform/lambda
API_URL=$(terraform output -raw api_gateway_url)
cd - > /dev/null

echo "Building Reminders SPA..."
export VITE_COGNITO_USER_POOL_ID="${COGNITO_USER_POOL_ID}"
export VITE_COGNITO_CLIENT_ID="${COGNITO_CLIENT_ID}"
export VITE_API_URL="${API_URL}"
export VITE_FLASHCARDS_URL="https://flashcards.poulomi-subhayan.click/"

npm ci
npm run build

echo "Syncing to S3 bucket: $S3_BUCKET"
aws s3 sync dist/ s3://${S3_BUCKET}/ --delete

echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_ID} --paths '/*'

echo "Deployment complete: $WEBSITE_URL"
