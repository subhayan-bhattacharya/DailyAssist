variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  type        = string
  default     = "eu-central-1_l5zXIFCUv"
}

variable "domain_name" {
  description = "Custom domain name for the frontend"
  type        = string
  default     = "poulomi-subhayan.click"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for frontend static assets"
  type        = string
  default     = "poulomi-subhayan.click"
}
