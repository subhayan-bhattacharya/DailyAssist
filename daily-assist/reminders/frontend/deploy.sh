#!/bin/bash
set -e

echo "Building Reminders SPA..."
npm ci
npm run build

# Fetch outputs from the reminders infrastructure
echo "Fetching infrastructure outputs..."
cd ../terraform/frontend
S3_BUCKET=$(terraform output -raw s3_bucket_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
cd - > /dev/null

echo "Syncing to S3 bucket: $S3_BUCKET"
aws s3 sync dist/ s3://${S3_BUCKET}/ --delete

echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_ID} --paths '/*'

echo "Deployment complete!"
