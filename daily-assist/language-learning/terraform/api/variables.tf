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

variable "lambda_source_dir" {
  description = "Path to language-learning source directory relative to this module"
  type        = string
  default     = "../.."
}

variable "database_url_secret_name" {
  description = "Secrets Manager secret name for the Neon database URL (created by scheduled terraform)"
  type        = string
  default     = "daily-assist/language-learning/database-url"
}

variable "frontend_origin" {
  description = "Allowed frontend origin for API Gateway CORS responses"
  type        = string
  default     = "https://flashcards.poulomi-subhayan.click"
}
