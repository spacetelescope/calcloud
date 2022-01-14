#! /bin/bash

# simple convenience script for printing all images in the central ECR
source deploy_vars.sh

awsudo $ADMIN_ARN aws ecr list-images --registry-id $ECR_ACCOUNT_ID --repository-name $IMAGE_REPO 