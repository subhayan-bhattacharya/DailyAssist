#!/bin/bash
set -e

# Fetch outputs from the shared infrastructure
echo "Fetching shared infrastructure outputs..."
cd ../../shared-infra/frontend
COGNITO_USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)
cd - > /dev/null

# Fetch outputs from the language learning frontend infrastructure
echo "Fetching frontend infrastructure outputs..."
cd ../terraform/frontend
S3_BUCKET=$(terraform output -raw s3_bucket_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
COGNITO_CLIENT_ID=$(terraform output -raw cognito_client_id)
cd - > /dev/null

# Fetch API URL from language-learning backend terraform
cd ../terraform/api
LANGUAGE_API_URL=$(terraform output -raw api_gateway_url)
cd - > /dev/null

echo "Building Language Learning SPA..."
export VITE_BASE_PATH="/"
export VITE_COGNITO_USER_POOL_ID="${COGNITO_USER_POOL_ID}"
export VITE_COGNITO_CLIENT_ID="${COGNITO_CLIENT_ID}"
export VITE_API_URL="${LANGUAGE_API_URL}"

npm ci
npm run build

echo "Syncing to S3 bucket: $S3_BUCKET"
aws s3 sync dist/ s3://${S3_BUCKET}/ --delete

echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_ID} --paths '/*'

echo "Deployment complete!"
