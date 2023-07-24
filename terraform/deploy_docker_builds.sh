#! /bin/bash

source deploy_vars.sh

source deploy_checkout_repos.sh

# imageTags are constructed in deploy_vars.sh

# check if the tag(s) we're building for exist already; if so, we'll stop and warn the user
/bin/bash deploy_existing_imageTag_check.sh ${CALDP_ECR_TAG//unscanned-/} ${PREDICT_ECR_TAG//unscanned-/} ${TRAINING_ECR_TAG//unscanned-/} ${AMIROTATION_ECR_TAG//unscanned-/} 
existingImage=$?

if [[ $existingImage -eq 1 ]]; then
    echo "At least one image is already tagged." 
    echo "Use deploy_ecr_image_delete.sh to remove the image if you really want to push to the same tag."
    echo "use deploy_print_central_images.sh to get a list of central ECR images, with SHA256 and tags"
    cd ${CALCLOUD_BUILD_DIR}/terraform
    source deploy_cleanup.sh
    exit 1
fi

# naming is confusing here but "modeling" directory plus "training" image is correct
cd ${CALCLOUD_BUILD_DIR}/modeling
cp /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem certs/tls-ca-bundle.pem # copy the cert from CI node AMI
set -o pipefail && docker build -f Dockerfile -t ${TRAINING_DOCKER_IMAGE} .
training_docker_build_status=$?
if [[ $training_docker_build_status -ne 0 ]]; then
    echo "training job docker build failed; exiting"
    exit 1
fi

# jobPredict lambda env
cd ${CALCLOUD_BUILD_DIR}/lambda/JobPredict
cp /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem certs/tls-ca-bundle.pem # copy the cert from CI node AMI
set -o pipefail && docker build -f Dockerfile -t ${PREDICT_DOCKER_IMAGE} .
model_docker_build_status=$?
if [[ $model_docker_build_status -ne 0 ]]; then
    echo "predict lambda env docker build failed; exiting"
    exit 1
fi

# caldp image
cd ${CALDP_BUILD_DIR}
cp /etc/ssl/certs/ca-bundle.crt tls-ca-bundle.pem # copy the cert from CI node AMI
set -o pipefail && docker build -f Dockerfile -t ${CALDP_DOCKER_IMAGE} --build-arg CAL_BASE_IMAGE="${CAL_BASE_IMAGE}"  .
caldp_docker_build_status=$?
if [[ $caldp_docker_build_status -ne 0 ]]; then
    echo "caldp docker build failed; exiting"
    exit 1
fi

# amirotation image
cd ${CALCLOUD_BUILD_DIR}/terraform
source deploy_ami_rotation_codebuild_image.sh # build, scan, and tag AMIROTATION image

# need to "log in" to ecr to push or pull the images
awsudo $ADMIN_ARN aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $repo_url

echo Pushing  ${TRAINING_DOCKER_IMAGE}
docker push ${TRAINING_DOCKER_IMAGE}

echo Pushing ${PREDICT_DOCKER_IMAGE} 
docker push ${PREDICT_DOCKER_IMAGE}

echo Pushing ${CALDP_DOCKER_IMAGE}
docker push ${CALDP_DOCKER_IMAGE}

cd ${CALCLOUD_BUILD_DIR}/terraform
source deploy_cleanup.sh
