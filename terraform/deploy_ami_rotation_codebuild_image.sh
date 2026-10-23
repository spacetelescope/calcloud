#! /bin/bash

# Script for building the AMI rotation codebuild image, called from deploy_docker_builds.sh

source deploy_vars.sh

source deploy_checkout_repos.sh

cd ${CALCLOUD_BUILD_DIR}/iac/codebuild
pwd

source hst_admin_role_shim.sh cert-update

set -o pipefail && docker build -f Dockerfile -t ${AMIROTATION_DOCKER_IMAGE_UNSCANNED} --build-arg aws_env="${aws_env}" --build-arg CALCLOUD_VER="${CALCLOUD_VER}" .
amirotation_docker_build_status=$?

if [[ $amirotation_docker_build_status -ne 0 ]]; then
    echo "AMI Rotation docker build failed; exiting"
    exit 1
fi

# need to "log in" to ecr to push or pull the images
AWS_PROFILE=hst_reprocessing_admin_role aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $repo_url

echo Pushing ${AMIROTATION_DOCKER_IMAGE_UNSCANNED}
docker push ${AMIROTATION_DOCKER_IMAGE_UNSCANNED}
#echo "Pushed unscanned AMI Rotation codebuild image"

cd ${CALCLOUD_BUILD_DIR}/terraform
pwd

echo "Sleeping for 30 seconds before scanning"
sleep 30

python3.13 ami-rotation-image-scan.py
amirotation_image_scan_status=$?

# exit status 3 from the scan script means fatal vulnerabilities were found; other nonzero values mean errors
if [ $amirotation_image_scan_status -eq 0 ]
then
        echo "Image scan successful."
        if ! ./deploy_image_promote.sh --old-tag $AMIROTATION_ECR_TAG_UNSCANNED $AMIROTATION_ECR_TAG_LATEST
        then
                echo "Failed to tag scanned image as ${AMIROTATION_ECR_TAG_LATEST}; exiting"
                exit 1
        fi
        echo "Tagged latest successfully scanned image"
        ./deploy_ecr_image_delete.sh $AMIROTATION_ECR_TAG_UNSCANNED
        echo "Deleted unscanned tag"
else
        if [ $amirotation_image_scan_status -eq 3 ]
        then
                echo "Image scan found fatal vulnerabilities in ${AMIROTATION_ECR_TAG_UNSCANNED}."
        else
                echo "Could not get scan results for ${AMIROTATION_ECR_TAG_UNSCANNED} (exit status ${amirotation_image_scan_status})."
        fi
        if [ ! -t 0 ]
        then
                echo "No interactive terminal to confirm using previously scanned image ${AMIROTATION_ECR_TAG_LATEST}; exiting"
                exit 1
        fi
        read -r -p "Proceed with previously scanned image ${AMIROTATION_ECR_TAG_LATEST}? Type 'yes' to continue: " use_previous_image
        if [ "$use_previous_image" != "yes" ]
        then
                echo "Not using previously scanned image; exiting"
                exit 1
        fi
        echo "Using previously scanned image ${AMIROTATION_ECR_TAG_LATEST}."
fi

if ! ./deploy_image_promote.sh --old-tag $AMIROTATION_ECR_TAG_LATEST $AMIROTATION_ECR_TAG
then
        echo "Failed to tag ${AMIROTATION_ECR_TAG_LATEST} as ${AMIROTATION_ECR_TAG}; exiting"
        exit 1
fi