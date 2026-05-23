variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-central-1"
}

variable "lambda_iam_role_name" {
  description = "Name of the existing IAM role for Lambda execution"
  type        = string
  default     = "CoudWatchAndDynamodbAccessRoleForLambda"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 900
}

variable "lambda_memory_size" {
  description = "Lambda memory in MB"
  type        = number
  default     = 512
}

variable "lambda_reserved_concurrency" {
  description = "Reserved concurrency for the enrichment Lambda"
  type        = number
  default     = 1
}

variable "enrichment_function_name" {
  description = "Name of the language-learning enrichment Lambda function"
  type        = string
  default     = "language-learning-dev-runEnrichment"
}

variable "ecr_repository_name" {
  description = "Name of the ECR repository for the enrichment Lambda image. ECR repository names must be lowercase."
  type        = string
  default     = "language-learning-dev-runenrichment"
}

variable "enrichment_schedule" {
  description = "Cron schedule for the enrichment EventBridge rule"
  type        = string
  default     = "cron(0 2 * * ? *)"
}

variable "openai_model" {
  description = "OpenAI model used by the enrichment job"
  type        = string
  default     = "gpt-4o-mini"
}

variable "enrichment_batch_limit" {
  description = "Maximum words to enrich in a single scheduled invocation"
  type        = number
  default     = 15
}

variable "database_url" {
  description = "Database URI to store in Secrets Manager"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key to store in Secrets Manager"
  type        = string
  sensitive   = true
}

variable "lambda_source_dir" {
  description = "Path to the language-learning source directory relative to this module"
  type        = string
  default     = "../.."
}
