variable "aws_region" {
  description = "AWS region for Terraform state resources"
  type        = string
  default     = "eu-central-1"
}

variable "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  type        = string
  default     = "dailyassist-terraform-state-dev"
}
