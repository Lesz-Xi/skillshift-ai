#!/bin/bash

# MLBB Coach AI - CDN Deployment Script
# Deploys CloudFront distribution and configures S3 buckets

set -e

echo "🌐 MLBB Coach AI - CDN Deployment"
echo "=================================="

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
S3_BUCKET_IMAGES="${S3_BUCKET_IMAGES:-mlbb-coach-ai-images}"
S3_BUCKET_ASSETS="${S3_BUCKET_ASSETS:-mlbb-coach-ai-assets}"
S3_BUCKET_LOGS="${S3_BUCKET_LOGS:-mlbb-coach-ai-logs}"
DOMAIN_NAME="${DOMAIN_NAME:-mlbb-coach-ai.com}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install AWS CLI first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS credentials verified"

# Create S3 buckets
echo "📦 Creating S3 buckets..."

create_bucket() {
    local bucket_name=$1
    local purpose=$2
    
    echo "Creating $purpose bucket: $bucket_name"
    
    # Create bucket
    if [ "$AWS_REGION" != "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "$bucket_name" \
            --region "$AWS_REGION" \
            --create-bucket-configuration LocationConstraint="$AWS_REGION" || true
    else
        aws s3api create-bucket \
            --bucket "$bucket_name" \
            --region "$AWS_REGION" || true
    fi
    
    # Configure bucket settings based on purpose
    if [ "$purpose" = "images" ] || [ "$purpose" = "assets" ]; then
        # Public read access for content buckets
        aws s3api put-bucket-policy \
            --bucket "$bucket_name" \
            --policy "{
                \"Version\": \"2012-10-17\",
                \"Statement\": [
                    {
                        \"Sid\": \"PublicReadGetObject\",
                        \"Effect\": \"Allow\",
                        \"Principal\": \"*\",
                        \"Action\": \"s3:GetObject\",
                        \"Resource\": \"arn:aws:s3:::$bucket_name/*\"
                    }
                ]
            }"
        
        # Enable CORS
        aws s3api put-bucket-cors \
            --bucket "$bucket_name" \
            --cors-configuration "{
                \"CORSRules\": [
                    {
                        \"AllowedHeaders\": [\"*\"],
                        \"AllowedMethods\": [\"GET\", \"HEAD\"],
                        \"AllowedOrigins\": [\"*\"],
                        \"ExposeHeaders\": [\"ETag\"],
                        \"MaxAgeSeconds\": 3600
                    }
                ]
            }"
            
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "$bucket_name" \
            --versioning-configuration Status=Enabled
            
        # Set lifecycle policy
        aws s3api put-bucket-lifecycle-configuration \
            --bucket "$bucket_name" \
            --lifecycle-configuration "{
                \"Rules\": [
                    {
                        \"ID\": \"DeleteOldVersions\",
                        \"Status\": \"Enabled\",
                        \"NoncurrentVersionExpiration\": {
                            \"NoncurrentDays\": 30
                        }
                    }
                ]
            }"
    fi
    
    echo "✅ Bucket $bucket_name configured"
}

# Create all buckets
create_bucket "$S3_BUCKET_IMAGES" "images"
create_bucket "$S3_BUCKET_ASSETS" "assets"
create_bucket "$S3_BUCKET_LOGS" "logs"

# Upload sample assets
echo "📁 Uploading sample assets..."

# Create sample directory structure
mkdir -p temp_assets/{heroes,icons,screenshots,css,js}

# Upload sample files (you would replace these with actual assets)
echo "/* MLBB Coach AI Styles */" > temp_assets/css/main.css
echo "// MLBB Coach AI Scripts" > temp_assets/js/main.js

# Upload to S3
aws s3 sync temp_assets/ s3://$S3_BUCKET_ASSETS/ --delete

# Clean up temp directory
rm -rf temp_assets

echo "✅ Sample assets uploaded"

# Create Origin Access Identity for CloudFront
echo "🔒 Creating CloudFront Origin Access Identity..."

OAI_RESPONSE=$(aws cloudfront create-origin-access-identity \
    --origin-access-identity-config "{
        \"CallerReference\": \"mlbb-coach-ai-$(date +%s)\",
        \"Comment\": \"MLBB Coach AI Origin Access Identity\"
    }")

OAI_ID=$(echo "$OAI_RESPONSE" | jq -r '.OriginAccessIdentity.Id')
echo "✅ Origin Access Identity created: $OAI_ID"

# Create CloudFront distribution
echo "☁️  Creating CloudFront distribution..."

# Generate unique caller reference
CALLER_REF="mlbb-coach-ai-$(date +%s)"

# Create distribution configuration
cat > cloudfront-config.json << EOF
{
    "CallerReference": "$CALLER_REF",
    "Comment": "MLBB Coach AI - Global CDN",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 2,
        "Items": [
            {
                "Id": "mlbb-assets-origin",
                "DomainName": "$S3_BUCKET_ASSETS.s3.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": "origin-access-identity/cloudfront/$OAI_ID"
                }
            },
            {
                "Id": "mlbb-images-origin",
                "DomainName": "$S3_BUCKET_IMAGES.s3.amazonaws.com",
                "S3OriginConfig": {
                    "OriginAccessIdentity": "origin-access-identity/cloudfront/$OAI_ID"
                }
            }
        ]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "mlbb-assets-origin",
        "ViewerProtocolPolicy": "redirect-to-https",
        "MinTTL": 0,
        "DefaultTTL": 86400,
        "MaxTTL": 31536000,
        "ForwardedValues": {
            "QueryString": false,
            "Cookies": {"Forward": "none"}
        },
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        },
        "Compress": true
    },
    "CacheBehaviors": {
        "Quantity": 1,
        "Items": [
            {
                "PathPattern": "/images/*",
                "TargetOriginId": "mlbb-images-origin",
                "ViewerProtocolPolicy": "redirect-to-https",
                "MinTTL": 0,
                "DefaultTTL": 604800,
                "MaxTTL": 31536000,
                "ForwardedValues": {
                    "QueryString": true,
                    "Cookies": {"Forward": "none"}
                },
                "Compress": true
            }
        ]
    },
    "CustomErrorResponses": {
        "Quantity": 2,
        "Items": [
            {
                "ErrorCode": 404,
                "ResponsePagePath": "/404.html",
                "ResponseCode": "404",
                "ErrorCachingMinTTL": 300
            },
            {
                "ErrorCode": 500,
                "ResponsePagePath": "/500.html",
                "ResponseCode": "500",
                "ErrorCachingMinTTL": 0
            }
        ]
    },
    "Logging": {
        "Enabled": true,
        "IncludeCookies": false,
        "Bucket": "$S3_BUCKET_LOGS.s3.amazonaws.com",
        "Prefix": "cloudfront-logs/"
    },
    "Enabled": true,
    "PriceClass": "PriceClass_100"
}
EOF

# Create CloudFront distribution
DISTRIBUTION_RESPONSE=$(aws cloudfront create-distribution \
    --distribution-config file://cloudfront-config.json)

DISTRIBUTION_ID=$(echo "$DISTRIBUTION_RESPONSE" | jq -r '.Distribution.Id')
DISTRIBUTION_DOMAIN=$(echo "$DISTRIBUTION_RESPONSE" | jq -r '.Distribution.DomainName')

echo "✅ CloudFront distribution created:"
echo "   Distribution ID: $DISTRIBUTION_ID"
echo "   Domain: $DISTRIBUTION_DOMAIN"

# Clean up config file
rm -f cloudfront-config.json

# Update bucket policies to allow OAI access
echo "🔐 Updating bucket policies for OAI access..."

for bucket in "$S3_BUCKET_ASSETS" "$S3_BUCKET_IMAGES"; do
    aws s3api put-bucket-policy \
        --bucket "$bucket" \
        --policy "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [
                {
                    \"Sid\": \"AllowCloudFrontAccess\",
                    \"Effect\": \"Allow\",
                    \"Principal\": {
                        \"AWS\": \"arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity $OAI_ID\"
                    },
                    \"Action\": \"s3:GetObject\",
                    \"Resource\": \"arn:aws:s3:::$bucket/*\"
                }
            ]
        }"
done

echo "✅ Bucket policies updated"

# Wait for distribution to be deployed
echo "⏳ Waiting for CloudFront distribution to be deployed..."
echo "   This may take 10-15 minutes..."

aws cloudfront wait distribution-deployed --id "$DISTRIBUTION_ID"

echo "🎉 CDN deployment completed successfully!"
echo ""
echo "📊 Deployment Summary:"
echo "====================="
echo "S3 Buckets:"
echo "  - Images: s3://$S3_BUCKET_IMAGES"
echo "  - Assets: s3://$S3_BUCKET_ASSETS"
echo "  - Logs: s3://$S3_BUCKET_LOGS"
echo ""
echo "CloudFront Distribution:"
echo "  - ID: $DISTRIBUTION_ID"
echo "  - Domain: $DISTRIBUTION_DOMAIN"
echo "  - Status: Deployed"
echo ""
echo "🔗 Access URLs:"
echo "  - Assets: https://$DISTRIBUTION_DOMAIN/"
echo "  - Images: https://$DISTRIBUTION_DOMAIN/images/"
echo ""
echo "💡 Next steps:"
echo "  1. Update your application configuration with the CDN URLs"
echo "  2. Upload your actual assets to the S3 buckets"
echo "  3. Configure custom domain (optional)"
echo "  4. Set up monitoring and alerts"

# Save configuration for later use
cat > cdn-config.env << EOF
# MLBB Coach AI CDN Configuration
export AWS_REGION="$AWS_REGION"
export S3_BUCKET_IMAGES="$S3_BUCKET_IMAGES"
export S3_BUCKET_ASSETS="$S3_BUCKET_ASSETS"
export S3_BUCKET_LOGS="$S3_BUCKET_LOGS"
export CLOUDFRONT_DISTRIBUTION_ID="$DISTRIBUTION_ID"
export CLOUDFRONT_DOMAIN="$DISTRIBUTION_DOMAIN"
export ORIGIN_ACCESS_IDENTITY="$OAI_ID"
EOF

echo ""
echo "📝 Configuration saved to cdn-config.env"
echo "   Source this file to use the CDN configuration:"
echo "   source cdn-config.env"
