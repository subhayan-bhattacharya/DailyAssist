variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "reminders"
}

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.13"
}

variable "lambda_handler" {
  description = "Lambda handler function"
  type        = string
  default     = "app.handler"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 128
}

variable "cognito_user_pool_arn" {
  description = "Cognito User Pool ARN"
  type        = string
  default     = "arn:aws:cognito-idp:eu-central-1:498129003450:userpool/eu-central-1_l5zXIFCUv"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
  default     = "Reminders"
}

variable "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  type        = string
  default     = "arn:aws:dynamodb:eu-central-1:498129003450:table/Reminders"
}

variable "api_gateway_name" {
  description = "Existing API Gateway REST API name"
  type        = string
  default     = "daily_assist_reminders"
}

variable "lambda_iam_role_name" {
  description = "Existing IAM role name for Lambda"
  type        = string
  default     = "CoudWatchAndDynamodbAccessRoleForLambda"
}

variable "lambda_source_dir" {
  description = "Directory containing Lambda source code (relative to terraform/lambda/)"
  type        = string
  default     = "../../.."
}

variable "image_tag" {
  description = "Docker image tag (defaults to 'latest', but can be set to version number)"
  type        = string
  default     = "latest"
}
