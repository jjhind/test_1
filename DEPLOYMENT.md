# AWS Lambda Deployment Guide

This guide walks you through deploying the Website Monitor to AWS Lambda using Terraform and GitHub Actions.

## Prerequisites

- AWS Account
- GitHub Account
- AWS CLI installed (for manual deployment)
- Terraform installed (for manual deployment)

## Deployment Options

### Option 1: GitHub Actions (Recommended)

This is the easiest method - push to GitHub and let Actions handle everything.

#### Step 1: Set up AWS Credentials

1. Create an IAM user in AWS with the following permissions:
   - `AmazonS3FullAccess`
   - `AWSLambda_FullAccess`
   - `IAMFullAccess`
   - `CloudWatchLogsFullAccess`
   - `AmazonEventBridgeFullAccess`

2. Generate access keys for this user

#### Step 2: Create S3 Bucket for Terraform State

```bash
aws s3 mb s3://my-terraform-state-bucket-unique-name --region us-east-1
```

Enable versioning:
```bash
aws s3api put-bucket-versioning \
  --bucket my-terraform-state-bucket-unique-name \
  --versioning-configuration Status=Enabled
```

#### Step 3: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `TF_STATE_BUCKET` | S3 bucket for Terraform state | `my-terraform-state-bucket` |
| `WEBSITE_URL` | URL to monitor | `https://www.sofasandstuff.com/outlet` |
| `FROM_EMAIL` | Email to send from | `your-email@gmail.com` |
| `EMAIL_PASSWORD` | Email app password | `your-app-password` |
| `TO_EMAIL` | Email to receive notifications | `notifications@example.com` |

#### Step 4: Push to GitHub

```bash
git add .
git commit -m "Configure Lambda deployment"
git push origin main
```

The GitHub Action will automatically:
1. Build the Lambda package
2. Run Terraform plan
3. Deploy to AWS
4. Test the Lambda function
5. Show deployment summary

#### Step 5: Monitor Deployment

- Go to Actions tab in GitHub to watch the deployment
- Check the deployment summary at the end
- Review CloudWatch Logs in AWS

---

### Option 2: Manual Deployment with Terraform

For local deployment or more control.

#### Step 1: Build Lambda Package

```bash
./scripts/build_lambda.sh
```

#### Step 2: Configure Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your settings:
- Website URL
- Email configuration
- AWS region
- Schedule (hourly, daily, etc.)

#### Step 3: Initialize Terraform

```bash
# Option A: Local state (for testing)
terraform init

# Option B: Remote state (recommended for production)
terraform init \
  -backend-config="bucket=my-terraform-state-bucket" \
  -backend-config="key=website-monitor/terraform.tfstate" \
  -backend-config="region=us-east-1"
```

#### Step 4: Review Plan

```bash
terraform plan
```

Review all resources that will be created:
- Lambda function
- S3 bucket for state
- EventBridge rule
- IAM roles and policies
- CloudWatch log group

#### Step 5: Deploy

```bash
terraform apply
```

Type `yes` when prompted.

#### Step 6: Verify Deployment

```bash
# Get Lambda function name
terraform output lambda_function_name

# Test the function
aws lambda invoke \
  --function-name $(terraform output -raw lambda_function_name) \
  --payload '{}' \
  response.json

cat response.json
```

---

## Configuration

### Schedule Expressions

Change `schedule_expression` in `terraform.tfvars`:

```hcl
# Every hour
schedule_expression = "rate(1 hour)"

# Every 30 minutes
schedule_expression = "rate(30 minutes)"

# Every day at 9 AM UTC
schedule_expression = "cron(0 9 * * ? *)"

# Every weekday at 8 AM UTC
schedule_expression = "cron(0 8 ? * MON-FRI *)"

# Every 6 hours
schedule_expression = "rate(6 hours)"
```

### Email Setup (Gmail)

1. Enable 2-Factor Authentication
2. Generate App Password:
   - https://myaccount.google.com/security
   - "2-Step Verification" → "App passwords"
   - Generate password for "Mail"
3. Use the app password in `terraform.tfvars` or GitHub Secrets

---

## Monitoring & Debugging

### View Lambda Logs

```bash
# Via AWS CLI
aws logs tail /aws/lambda/website-item-monitor --follow

# Or in AWS Console
# CloudWatch → Log groups → /aws/lambda/website-item-monitor
```

### Test Lambda Manually

```bash
# Invoke the function
aws lambda invoke \
  --function-name website-item-monitor \
  --payload '{}' \
  response.json

# View response
cat response.json
```

### Check EventBridge Rule

```bash
# List rules
aws events list-rules --name-prefix website-monitor

# Describe specific rule
aws events describe-rule --name website-monitor-schedule-prod
```

### View S3 State

```bash
# List state files
aws s3 ls s3://$(terraform output -raw state_bucket_name)/

# Download state file
aws s3 cp s3://$(terraform output -raw state_bucket_name)/items_state.json ./
```

---

## Cost Estimation

### AWS Lambda Pricing (Free Tier)

- **Requests**: 1M requests/month free
- **Compute**: 400,000 GB-seconds/month free

### Your Usage (Hourly Checks)

- Requests: ~720/month (24 × 30)
- Duration: ~5 seconds per invocation
- Memory: 256 MB
- Compute: ~900 GB-seconds/month

**Total Cost: $0** (well within free tier)

Even after free tier:
- ~$0.20/month for Lambda
- ~$0.10/month for CloudWatch Logs
- **Total: ~$0.30/month**

---

## Updating the Deployment

### Via GitHub Actions

1. Make changes to code
2. Commit and push to main branch
3. GitHub Actions automatically deploys

### Via Terraform

```bash
cd terraform

# Rebuild Lambda package if code changed
../scripts/build_lambda.sh

# Apply changes
terraform plan
terraform apply
```

---

## Customizing the Parser

If items aren't being detected, customize the HTML parser:

1. Edit `lambda_handler.py`
2. Modify the `parse_items()` method
3. Update the `product_selectors` list with correct CSS selectors
4. Redeploy

Example:
```python
product_selectors = [
    {
        'container': '.outlet-item',      # Adjust for your site
        'title': '.product-name',         # Adjust for your site
        'price': '.sale-price',           # Adjust for your site
        'link': 'a.product-link'          # Adjust for your site
    }
]
```

---

## Troubleshooting

### Issue: No items detected

**Solution:**
- Check CloudWatch logs
- Test the URL manually in browser
- Customize the parser selectors
- Verify website is accessible

### Issue: Email not sending

**Solution:**
- Verify email credentials in Terraform vars or GitHub Secrets
- Check for Gmail app password (not regular password)
- Review Lambda logs for SMTP errors
- Ensure SMTP_SERVER and SMTP_PORT are correct

### Issue: Lambda timeout

**Solution:**
- Increase `lambda_timeout` in `terraform.tfvars`
- Default is 300 seconds (5 minutes)

### Issue: Permission denied errors

**Solution:**
- Check IAM role has correct permissions
- Verify S3 bucket policy
- Review CloudWatch Logs permissions

---

## Cleanup / Destroy

To remove all AWS resources:

```bash
cd terraform
terraform destroy
```

Type `yes` when prompted.

This will delete:
- Lambda function
- S3 bucket (if empty)
- EventBridge rule
- IAM roles
- CloudWatch log groups

---

## Security Best Practices

1. **Never commit secrets** - Use GitHub Secrets or AWS Secrets Manager
2. **Use app passwords** - Not your main email password
3. **Rotate credentials** - Change passwords periodically
4. **Restrict IAM** - Use least-privilege permissions
5. **Enable MFA** - On AWS account
6. **Monitor costs** - Set up billing alerts

---

## Next Steps

1. Monitor first few runs in CloudWatch Logs
2. Verify email notifications work
3. Customize parser if needed
4. Adjust schedule as needed
5. Add more websites to monitor (duplicate Lambda with different config)

---

## Support

- Check CloudWatch Logs first
- Review Terraform output for errors
- Test Lambda function manually
- Verify website URL is accessible
- Check email configuration

For issues with the code, create an issue in the repository.
