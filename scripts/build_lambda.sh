#!/bin/bash
set -e

echo "Building Lambda deployment package..."

# Clean up previous build
rm -rf lambda_package
mkdir -p lambda_package

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt -t lambda_package/

# Copy Lambda handler
echo "Copying Lambda handler..."
cp lambda_handler.py lambda_package/

echo "Lambda package built successfully in lambda_package/"
echo "Ready for Terraform deployment"
