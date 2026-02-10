output "cognito_client_id" {
  description = "Cognito App Client ID for the frontend"
  value       = aws_cognito_user_pool_client.frontend.id
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = data.aws_cognito_user_pool.main.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (use for cache invalidation)"
  value       = aws_cloudfront_distribution.frontend.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "s3_bucket_name" {
  description = "S3 bucket name for frontend assets"
  value       = aws_s3_bucket.frontend.id
}

output "website_url" {
  description = "Website URL"
  value       = "https://${var.domain_name}"
}
