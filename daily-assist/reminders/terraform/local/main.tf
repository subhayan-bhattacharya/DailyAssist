terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure AWS provider to use DynamoDB Local
provider "aws" {
  region                      = "eu-central-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    dynamodb = "http://localhost:8000"
  }
}

# Create Reminders table in DynamoDB Local
resource "aws_dynamodb_table" "reminders" {
  name         = "Reminders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "reminder_id"
  range_key    = "user_id"

  attribute {
    name = "reminder_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "reminder_title"
    type = "S"
  }

  global_secondary_index {
    name            = "UserIdReminderTitleGsi2"
    hash_key        = "user_id"
    range_key       = "reminder_title"
    projection_type = "INCLUDE"
    non_key_attributes = [
      "reminder_expiration_date_time",
      "reminder_id",
      "reminder_tags"
    ]
  }

  tags = {
    Name        = "Reminders"
    Environment = "local"
  }
}
