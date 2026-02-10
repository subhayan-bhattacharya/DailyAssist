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

variable "lambda_layer_name" {
  description = "Name of the existing Lambda layer with Python dependencies"
  type        = string
  default     = "reminders-dev-managed-layer"
}

variable "lambda_runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Lambda memory in MB"
  type        = number
  default     = 128
}

variable "send_reminders_function_name" {
  description = "Name of the send reminders Lambda function"
  type        = string
  default     = "reminders-dev-queryAndSendReminders"
}

variable "delete_expired_function_name" {
  description = "Name of the delete expired reminders Lambda function"
  type        = string
  default     = "reminders-dev-deleteExpiredReminders"
}

variable "send_reminders_schedule" {
  description = "Cron schedule for the send reminders EventBridge rule"
  type        = string
  default     = "cron(0 5 * * ? *)"
}

variable "delete_expired_schedule" {
  description = "Cron schedule for the delete expired reminders EventBridge rule"
  type        = string
  default     = "cron(00 7 ? * 1 *)"
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID passed in the send reminders event input"
  type        = string
  default     = "eu-central-1_l5zXIFCUv"
}

variable "global_message_arn" {
  description = "Global SNS topic ARN for DailyAssist reminders"
  type        = string
  default     = "arn:aws:sns:eu-central-1:498129003450:DailyAssistReminders"
}

variable "users" {
  description = "List of users with their SNS topic ARNs"
  type = list(object({
    username    = string
    message_arn = string
  }))
  default = [
    {
      username    = "Subhayan"
      message_arn = "arn:aws:sns:eu-central-1:498129003450:DailyAssistRemindersSubhayan"
    },
    {
      username    = "Poulomi"
      message_arn = "arn:aws:sns:eu-central-1:498129003450:DailyAssistRemindersPoulomi"
    }
  ]
}

variable "lambda_source_dir" {
  description = "Path to the reminders source directory relative to this module"
  type        = string
  default     = "../../.."
}
