terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  backend "s3" {
    # Configure via backend config file or environment variables
    # Example: terraform init -backend-config="bucket=my-terraform-state"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "website-monitor"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# S3 bucket for state storage
resource "aws_s3_bucket" "state" {
  bucket = "${var.project_name}-state-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name = "Website Monitor State Storage"
  }
}

# Enable versioning for state bucket
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access to state bucket
resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "Website Monitor Lambda Logs"
  }
}

# IAM role for Lambda
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "Website Monitor Lambda Role"
  }
}

# IAM policy for Lambda
resource "aws_iam_role_policy" "lambda" {
  name = "${var.project_name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.lambda.arn}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.state.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.state.arn
        ]
      }
    ]
  })
}

# Create deployment package
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda_package"
  output_path = "${path.module}/lambda_function.zip"
}

# Lambda function
resource "aws_lambda_function" "monitor" {
  filename         = data.archive_file.lambda.output_path
  function_name    = var.lambda_function_name
  role            = aws_iam_role.lambda.arn
  handler         = "lambda_handler.lambda_handler"
  source_code_hash = data.archive_file.lambda.output_base64sha256
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  environment {
    variables = {
      WEBSITE_NAME    = var.website_name
      WEBSITE_URL     = var.website_url
      STATE_BUCKET    = aws_s3_bucket.state.id
      STATE_KEY       = var.state_key
      EMAIL_ENABLED   = var.email_enabled
      SMTP_SERVER     = var.smtp_server
      SMTP_PORT       = var.smtp_port
      FROM_EMAIL      = var.from_email
      EMAIL_PASSWORD  = var.email_password
      TO_EMAIL        = var.to_email
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy.lambda
  ]

  tags = {
    Name = "Website Monitor Lambda"
  }
}

# EventBridge rule for scheduling
resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${var.project_name}-schedule-${var.environment}"
  description         = "Trigger website monitor on schedule"
  schedule_expression = var.schedule_expression

  tags = {
    Name = "Website Monitor Schedule"
  }
}

# EventBridge target
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "WebsiteMonitorLambda"
  arn       = aws_lambda_function.monitor.arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}

# Optional: SNS topic for alerts (if you want to receive deployment notifications)
resource "aws_sns_topic" "alerts" {
  count = var.enable_sns_alerts ? 1 : 0
  name  = "${var.project_name}-alerts-${var.environment}"

  tags = {
    Name = "Website Monitor Alerts"
  }
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count     = var.enable_sns_alerts ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}
