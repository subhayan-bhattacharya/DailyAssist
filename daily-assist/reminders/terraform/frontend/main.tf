terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket = "dailyassist-terraform-state-dev"
    key    = "frontend/terraform.tfstate"
    region = "eu-central-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Reference the existing Cognito User Pool
data "aws_cognito_user_pool" "main" {
  user_pool_id = var.cognito_user_pool_id
}

# Create a public App Client for the React frontend (no secret)
resource "aws_cognito_user_pool_client" "frontend" {
  name         = "reminders-frontend"
  user_pool_id = data.aws_cognito_user_pool.main.id

  # No client secret - required for browser-based apps
  generate_secret = false

  # Auth flows allowed
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # Token validity
  access_token_validity  = 1  # hours
  id_token_validity      = 1  # hours
  refresh_token_validity = 30 # days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # Prevent user existence errors (security best practice)
  prevent_user_existence_errors = "ENABLED"

  # Read and write attributes
  read_attributes  = ["email", "name", "preferred_username"]
  write_attributes = ["email", "name", "preferred_username"]
}
