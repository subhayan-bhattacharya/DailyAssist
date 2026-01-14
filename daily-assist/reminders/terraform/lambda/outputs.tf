output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.api.arn
}

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.lambda.repository_url
}

output "lambda_image_uri" {
  description = "Container image URI used by Lambda"
  value       = aws_lambda_function.api.image_uri
}

output "image_tag" {
  description = "Current Docker image tag (based on code hash)"
  value       = local.image_tag
}

output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = aws_api_gateway_stage.api.invoke_url
}

output "api_gateway_stage" {
  description = "API Gateway stage name"
  value       = aws_api_gateway_stage.api.stage_name
}

output "cognito_authorizer_id" {
  description = "ID of the Cognito authorizer"
  value       = aws_api_gateway_authorizer.cognito.id
}

output "api_endpoint" {
  description = "Full API endpoint URL"
  value       = "${aws_api_gateway_stage.api.invoke_url}/reminders"
}
