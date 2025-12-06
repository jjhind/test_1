output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.monitor.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.monitor.arn
}

output "state_bucket_name" {
  description = "Name of the S3 bucket storing state"
  value       = aws_s3_bucket.state.id
}

output "state_bucket_arn" {
  description = "ARN of the S3 state bucket"
  value       = aws_s3_bucket.state.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.lambda.name
}

output "schedule_expression" {
  description = "EventBridge schedule expression"
  value       = aws_cloudwatch_event_rule.schedule.schedule_expression
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.schedule.name
}

output "monitoring_url" {
  description = "URL being monitored"
  value       = var.website_url
}

output "sns_topic_arn" {
  description = "ARN of SNS topic for alerts (if enabled)"
  value       = var.enable_sns_alerts ? aws_sns_topic.alerts[0].arn : null
}
