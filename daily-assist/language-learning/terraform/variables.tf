variable "neon_api_key" {
  type        = string
  description = "The Neon API key"
  sensitive   = true
}

variable "neon_org_id" {
  type        = string
  description = "The Neon Organization ID"
}
