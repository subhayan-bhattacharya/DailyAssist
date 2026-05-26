variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-central-1"
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID (from shared-infra)"
  type        = string
  default     = "eu-central-1_l5zXIFCUv"
}

variable "route53_zone_id" {
  description = "Route 53 Hosted Zone ID"
  type        = string
  default     = "Z003866034TC2JG6TVG19"
}

variable "domain_name" {
  description = "Custom domain name for the Language Learning frontend"
  type        = string
  default     = "flashcards.poulomi-subhayan.click"
}
