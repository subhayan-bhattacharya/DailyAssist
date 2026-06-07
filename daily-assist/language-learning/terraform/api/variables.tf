variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "lambda_function_name" {
  description = "Name of the API Lambda function"
  type        = string
  default     = "language-learning-api"
}

variable "ecr_repository_name" {
  description = "Name of the ECR repository for the API Lambda image"
  type        = string
  default     = "language-learning-api"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Lambda memory in MB"
  type        = number
  default     = 256
}

variable "lambda_iam_role_name" {
  description = "Existing IAM role name for Lambda execution"
  type        = string
  default     = "CoudWatchAndDynamodbAccessRoleForLambda"
}


variable "database_url_secret_name" {
  description = "Secrets Manager secret name for the Neon database URL (created by scheduled terraform)"
  type        = string
  default     = "daily-assist/language-learning/database-url"
}

variable "frontend_origin" {
  description = "Allowed frontend origin for API Gateway CORS responses"
  type        = string
  default     = "https://poulomi-subhayan.click"
}

variable "cognito_user_pool_arn" {
  description = "Cognito User Pool ARN"
  type        = string
  default     = "arn:aws:cognito-idp:eu-central-1:498129003450:userpool/eu-central-1_l5zXIFCUv"
}

variable "api_image_tag" {
  description = "The image tag to use for the language learning api."
  type        = string
  default     = "0.0.1"
}
