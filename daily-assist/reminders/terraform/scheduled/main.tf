terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "DailyAssist"
      ManagedBy   = "Terraform"
      Application = "Reminders"
    }
  }
}

# ---------- Data sources ----------

data "aws_iam_role" "lambda_role" {
  name = var.lambda_iam_role_name
}

data "aws_lambda_layer_version" "dependencies" {
  layer_name = var.lambda_layer_name
}

# ---------- Lambda zip packaging ----------

data "archive_file" "lambda_code" {
  type        = "zip"
  output_path = "${path.module}/lambda_code.zip"

  source {
    content  = file("${path.module}/../../app.py")
    filename = "app.py"
  }

  dynamic "source" {
    for_each = fileset("${path.module}/../../core", "**/*.py")
    content {
      content  = file("${path.module}/../../core/${source.value}")
      filename = "core/${source.value}"
    }
  }
}

# ---------- Lambda functions ----------

resource "aws_lambda_function" "send_reminders" {
  function_name    = var.send_reminders_function_name
  role             = data.aws_iam_role.lambda_role.arn
  handler          = "app.lambda_query_and_send_reminders_handler"
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256

  layers = [data.aws_lambda_layer_version.dependencies.arn]
}

resource "aws_lambda_function" "delete_expired" {
  function_name    = var.delete_expired_function_name
  role             = data.aws_iam_role.lambda_role.arn
  handler          = "app.lambda_delete_expired_reminders_handler"
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size
  filename         = data.archive_file.lambda_code.output_path
  source_code_hash = data.archive_file.lambda_code.output_base64sha256

  layers = [data.aws_lambda_layer_version.dependencies.arn]
}

# ---------- EventBridge rules ----------

resource "aws_cloudwatch_event_rule" "send_reminders" {
  name                = "DailyAssistReminders"
  description         = "Reminders from daily assist application runs overnight"
  schedule_expression = var.send_reminders_schedule
}

resource "aws_cloudwatch_event_rule" "delete_expired" {
  name                = "deleteExpiredReminders"
  description         = "Delete reminders which are expired"
  schedule_expression = var.delete_expired_schedule
}

# ---------- EventBridge targets ----------

resource "aws_cloudwatch_event_target" "send_reminders" {
  rule = aws_cloudwatch_event_rule.send_reminders.name
  arn  = aws_lambda_function.send_reminders.arn

  input = jsonencode({
    users = [
      for user in var.users : {
        username    = user.username
        message_arn = user.message_arn
      }
    ]
    user_pool_id = var.cognito_user_pool_id
    message_arn  = var.global_message_arn
  })
}

resource "aws_cloudwatch_event_target" "delete_expired" {
  rule = aws_cloudwatch_event_rule.delete_expired.name
  arn  = aws_lambda_function.delete_expired.arn

  input = jsonencode({
    users = [
      for user in var.users : {
        username = user.username
      }
    ]
  })
}

# ---------- Lambda permissions for EventBridge ----------

resource "aws_lambda_permission" "send_reminders" {
  statement_id  = "AWSEvents_DailyAssistReminders_Idc132f301-54ce-424b-87e1-152fadfc5baf"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.send_reminders.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.send_reminders.arn
}

resource "aws_lambda_permission" "delete_expired" {
  statement_id  = "AWSEvents_deleteExpiredReminders_Id4adf1c71-d45f-4f21-a1d4-b317ce3f4f80"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.delete_expired.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.delete_expired.arn
}
