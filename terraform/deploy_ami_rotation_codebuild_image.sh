#! /bin/bash

# Script for building the AMI rotation codebuild image, called from deploy_docker_builds.sh

source deploy_vars.sh

source deploy_checkout_repos.sh

cd ${CALCLOUD_BUILD_DIR}/iac/codebuild
pwd

./copy-cert # copy the cert from CI node AMI and replace the cert in current dir

set -o pipefail && docker build -f Dockerfile -t ${AMIROTATION_DOCKER_IMAGE_UNSCANNED} --build-arg aws_env="${aws_env}" --build-arg CALCLOUD_VER="${CALCLOUD_VER}" .
amirotation_docker_build_status=$?

if [[ $amirotation_docker_build_status -ne 0 ]]; then
    echo "AMI Rotation docker build failed; exiting"
    exit 1
fi

# need to "log in" to ecr to push or pull the images
awsudo $ADMIN_ARN aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $repo_url

echo Pushing ${AMIROTATION_DOCKER_IMAGE_UNSCANNED}
docker push ${AMIROTATION_DOCKER_IMAGE_UNSCANNED}
#echo "Pushed unscanned AMI Rotation codebuild image"

cd ${CALCLOUD_BUILD_DIR}/terraform
pwd

python3 ami-rotation-image-scan.py
amirotation_image_scan_status=$?

if [ $amirotation_image_scan_status == 0 ]
then
        echo "Image scan successful."
        ./deploy_image_promote.sh --old-tag $AMIROTATION_ECR_TAG_UNSCANNED $AMIROTATION_ECR_TAG_LATEST
        echo "Tagged latest successfully scanned image"
        ./deploy_ecr_image_delete.sh $AMIROTATION_ECR_TAG_UNSCANNED
        echo "Deleted unscanned tag"
else
        echo "Image scan failed. Using previously scanned image."
fi

./deploy_image_promote.sh --old-tag $AMIROTATION_ECR_TAG_LATEST $AMIROTATION_ECR_TAG