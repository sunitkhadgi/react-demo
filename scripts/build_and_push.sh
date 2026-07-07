#!/bin/bash

set -e

AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="950846564503"
ECR_REPOSITORY="sunit-repo"

IMAGE_NAME="${ECR_REPOSITORY}"
IMAGE_TAG=$(date +%Y%m%d-%H%M%S)

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${IMAGE_NAME}"

echo "Logging into Amazon ECR..."

aws ecr get-login-password --region ${AWS_REGION} | \
docker login --username AWS --password-stdin ${ECR_URI}

echo "Building Docker image..."

cd /opt/docker-app

docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

echo "Tagging Docker image..."

docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}

echo "Pushing image to ECR..."

docker push ${ECR_URI}:${IMAGE_TAG}

echo "Docker image pushed successfully:"
echo "${ECR_URI}:${IMAGE_TAG}"
