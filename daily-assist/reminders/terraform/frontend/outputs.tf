output "cognito_client_id" {
  description = "Cognito App Client ID for the frontend"
  value       = aws_cognito_user_pool_client.frontend.id
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = data.aws_cognito_user_pool.main.id
}
