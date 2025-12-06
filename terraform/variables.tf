variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "website-monitor"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "website-item-monitor"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 300
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 256
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "schedule_expression" {
  description = "EventBridge schedule expression (e.g., 'rate(1 hour)' or 'cron(0 * * * ? *)')"
  type        = string
  default     = "rate(1 hour)"
}

variable "state_key" {
  description = "S3 key for state file"
  type        = string
  default     = "items_state.json"
}

# Website configuration
variable "website_name" {
  description = "Display name of the website being monitored"
  type        = string
  default     = "Sofas and Stuff Outlet"
}

variable "website_url" {
  description = "URL to monitor"
  type        = string
}

# Email configuration
variable "email_enabled" {
  description = "Enable email notifications"
  type        = string
  default     = "true"
}

variable "smtp_server" {
  description = "SMTP server address"
  type        = string
  default     = "smtp.gmail.com"
}

variable "smtp_port" {
  description = "SMTP server port"
  type        = string
  default     = "587"
}

variable "from_email" {
  description = "Email address to send from"
  type        = string
  sensitive   = true
}

variable "email_password" {
  description = "Email password or app password"
  type        = string
  sensitive   = true
}

variable "to_email" {
  description = "Email address to send notifications to"
  type        = string
}

# Optional SNS alerts
variable "enable_sns_alerts" {
  description = "Enable SNS topic for deployment alerts"
  type        = bool
  default     = false
}

variable "alert_email" {
  description = "Email for SNS alerts (only used if enable_sns_alerts is true)"
  type        = string
  default     = ""
}
