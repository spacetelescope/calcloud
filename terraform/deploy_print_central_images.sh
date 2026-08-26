#! /bin/bash

# simple convenience script for printing all images in the central ECR
source deploy_vars.sh

AWS_PROFILE=hst_reprocessing_admin_role aws ecr list-images --registry-id $ECR_ACCOUNT_ID --repository-name $IMAGE_REPO 