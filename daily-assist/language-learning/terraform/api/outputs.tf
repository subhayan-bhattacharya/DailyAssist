output "api_gateway_url" {
  description = "Base URL of the language learning API Gateway"
  value       = aws_api_gateway_stage.api.invoke_url
}

output "lambda_function_name" {
  description = "Name of the API Lambda function"
  value       = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  description = "ARN of the API Lambda function"
  value       = aws_lambda_function.api.arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.api.repository_url
}

output "image_tag" {
  description = "Docker image tag deployed"
  value       = local.image_tag
}
