source deploy_vars.sh

source deploy_checkout_repos.sh

# this is the tag that the image will have in AWS ECR
# CALDP_IMAGE_TAG="latest"

# currently, this script gets repo_url from the main deploy script.
# when we refactor to use the central ecr, we'll get the repo_url from ssm
# and it will be set in the deploy_vars.sh script
# if you want to run this script independently of deploy.sh, you'll need to set repo_url in the env manually
##### DOCKER IMAGE BUILDING #########
CALDP_DOCKER_IMAGE="${repo_url}:batch-${COMMON_IMAGE_TAG}"
PREDICT_DOCKER_IMAGE="${repo_url}:unscanned-predict-${COMMON_IMAGE_TAG}"
TRAINING_DOCKER_IMAGE="${repo_url}:unscanned-training-${COMMON_IMAGE_TAG}"

# naming is confusing here but "modeling" directory plus "training" image is correct
cd ${CALCLOUD_BUILD_DIR}/modeling
set -o pipefail && docker build -f Dockerfile -t ${TRAINING_DOCKER_IMAGE} .
training_docker_build_status=$?
if [[ $training_docker_build_status -ne 0 ]]; then
    echo "training job docker build failed; exiting"
    exit 1
fi

# jobPredict lambda env
cd ${CALCLOUD_BUILD_DIR}/lambda/JobPredict
set -o pipefail && docker build -f Dockerfile -t ${PREDICT_DOCKER_IMAGE} .
model_docker_build_status=$?
if [[ $model_docker_build_status -ne 0 ]]; then
    echo "predict lambda env docker build failed; exiting"
    exit 1
fi

# caldp image
cd ${CALDP_BUILD_DIR}
set -o pipefail && docker build -f Dockerfile -t ${CALDP_DOCKER_IMAGE} --build-arg CAL_BASE_IMAGE="${CAL_BASE_IMAGE}"  .
caldp_docker_build_status=$?
if [[ $caldp_docker_build_status -ne 0 ]]; then
    echo "caldp docker build failed; exiting"
    exit 1
fi

# need to "log in" to ecr to push or pull the images
awsudo $ADMIN_ARN aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $repo_url

docker push ${TRAINING_DOCKER_IMAGE}
docker push ${PREDICT_DOCKER_IMAGE}
docker push ${CALDP_DOCKER_IMAGE}

cd ${CALCLOUD_BUILD_DIR}/terraform
source deploy_cleanup.sh