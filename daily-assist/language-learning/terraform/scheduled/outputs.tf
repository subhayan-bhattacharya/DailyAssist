output "enrichment_function_arn" {
  description = "ARN of the language-learning enrichment Lambda function"
  value       = aws_lambda_function.enrichment.arn
}

output "enrichment_function_name" {
  description = "Name of the language-learning enrichment Lambda function"
  value       = aws_lambda_function.enrichment.function_name
}

output "enrichment_rule_arn" {
  description = "ARN of the enrichment EventBridge rule"
  value       = aws_cloudwatch_event_rule.enrichment.arn
}

output "ecr_repository_url" {
  description = "URL of the enrichment Lambda ECR repository"
  value       = aws_ecr_repository.enrichment.repository_url
}

output "lambda_image_uri" {
  description = "Container image URI used by the enrichment Lambda"
  value       = aws_lambda_function.enrichment.image_uri
}

output "image_tag" {
  description = "Current Docker image tag based on source and dependency lock hashes"
  value       = local.image_tag
}

output "database_url_secret_arn" {
  description = "ARN of the database URL secret"
  value       = aws_secretsmanager_secret.database_url.arn
}

output "openai_api_key_secret_arn" {
  description = "ARN of the OpenAI API key secret"
  value       = aws_secretsmanager_secret.openai_api_key.arn
}
