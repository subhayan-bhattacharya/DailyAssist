output "send_reminders_function_arn" {
  description = "ARN of the send reminders Lambda function"
  value       = aws_lambda_function.send_reminders.arn
}

output "delete_expired_function_arn" {
  description = "ARN of the delete expired reminders Lambda function"
  value       = aws_lambda_function.delete_expired.arn
}

output "send_reminders_rule_arn" {
  description = "ARN of the send reminders EventBridge rule"
  value       = aws_cloudwatch_event_rule.send_reminders.arn
}

output "delete_expired_rule_arn" {
  description = "ARN of the delete expired EventBridge rule"
  value       = aws_cloudwatch_event_rule.delete_expired.arn
}
