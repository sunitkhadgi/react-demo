#!/bin/bash
set -e

APP_DIR="/home/ubuntu"
ECR_REPOSITORY="shreyan-ignite"
IMAGE_TAG="latest"

cd "${APP_DIR}"

echo "Resolving AWS region from instance metadata..."
TOKEN=$(curl -sS -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 60")
AWS_REGION=$(curl -sS -H "X-aws-ec2-metadata-token: ${TOKEN}" \
  "http://169.254.169.254/latest/meta-data/placement/region")

# Fallback in case metadata lookup fails (e.g. CLI already has a region configured)
AWS_REGION="${AWS_REGION:-$(aws configure get region)}"

if [ -z "${AWS_REGION}" ]; then
  echo "ERROR: Could not determine AWS region." >&2
  exit 1
fi

echo "Using region: ${AWS_REGION}"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_URI="${ECR_REGISTRY}/${ECR_REPOSITORY}"

echo "Logging into ECR (${ECR_REGISTRY})..."
aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_REGISTRY}"

echo "Writing .env for docker-compose..."
cat > "${APP_DIR}/.env" << ENV
ECR_URI=${ECR_URI}
IMAGE_TAG=${IMAGE_TAG}
ENV

echo "Pulling latest image..."
docker compose pull

echo "Starting container..."
docker compose up -d
