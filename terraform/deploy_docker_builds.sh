#! /bin/bash

source deploy_vars.sh

source deploy_checkout_repos.sh

# imageTags are constructed in deploy_vars.sh

# check if the tag(s) we're building for exist already; if so, we'll stop and warn the user
/bin/bash deploy_existing_imageTag_check.sh ${CALDP_ECR_TAG} ${PREDICT_ECR_TAG} ${AMIROTATION_ECR_TAG}
existingImage=$?

if [[ $existingImage -eq 1 ]]; then
    echo "At least one image is already tagged."
    echo "Use deploy_ecr_image_delete.sh to remove the image if you really want to push to the same tag."
    echo "use deploy_print_central_images.sh to get a list of central ECR images, with SHA256 and tags"
    cd ${CALCLOUD_BUILD_DIR}/terraform
    source deploy_cleanup.sh
    exit 1
fi

# jobPredict lambda env
cd ${CALCLOUD_BUILD_DIR}/lambda/JobPredict
source hst_admin_role_shim.sh cert-update
cd ${CALCLOUD_BUILD_DIR}
PREDICT_BASE_IMAGE_REF=${PREDICT_BASE_IMAGE:-public.ecr.aws/lambda/python:3.13}
PREDICT_BASE_IMAGE_RESOLVED=$(resolve_base_image "JobPredict" "${PREDICT_BASE_IMAGE_REF}") || exit 1
export PREDICT_BASE_IMAGE_REF PREDICT_BASE_IMAGE_RESOLVED
echo "Building JobPredict from ${PREDICT_BASE_IMAGE_RESOLVED}"
set -o pipefail && docker build --pull -f lambda/JobPredict/Dockerfile -t ${PREDICT_DOCKER_IMAGE} \
    --build-arg PREDICT_BASE_IMAGE="${PREDICT_BASE_IMAGE_RESOLVED}" .
model_docker_build_status=$?
if [[ $model_docker_build_status -ne 0 ]]; then
    echo "predict lambda env docker build failed; exiting"
    exit 1
fi

# caldp image
cd ${CALDP_BUILD_DIR}
source hst_admin_role_shim.sh cert-update
CAL_BASE_IMAGE_REF=${CAL_BASE_IMAGE}
CAL_BASE_IMAGE_RESOLVED=$(resolve_base_image "CALDP" "${CAL_BASE_IMAGE_REF}") || exit 1
export CAL_BASE_IMAGE_REF CAL_BASE_IMAGE_RESOLVED
echo "Building CALDP from ${CAL_BASE_IMAGE_RESOLVED}"
set -o pipefail && docker build --pull -f Dockerfile -t ${CALDP_DOCKER_IMAGE} \
    --build-arg CAL_BASE_IMAGE="${CAL_BASE_IMAGE_RESOLVED}" .
caldp_docker_build_status=$?
if [[ $caldp_docker_build_status -ne 0 ]]; then
    echo "caldp docker build failed; exiting"
    exit 1
fi

# amirotation image
cd ${CALCLOUD_BUILD_DIR}/terraform
source deploy_ami_rotation_codebuild_image.sh # build, scan, and tag AMIROTATION image

# need to "log in" to ecr to push or pull the images
AWS_PROFILE=hst_reprocessing_admin_role aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $repo_url

echo Pushing ${PREDICT_DOCKER_IMAGE}
docker push ${PREDICT_DOCKER_IMAGE}

echo Pushing ${CALDP_DOCKER_IMAGE}
docker push ${CALDP_DOCKER_IMAGE}

cd ${CALCLOUD_BUILD_DIR}/terraform
if [[ -n "${IMAGE_BUILD_ID}" ]]; then
    if ! python3.13 write_image_release_manifest.py --apply; then
        echo "Failed to write release manifest for ${IMAGE_BUILD_ID}; exiting" >&2
        exit 1
    fi
fi

source deploy_cleanup.sh
