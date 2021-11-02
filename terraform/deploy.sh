#! /bin/bash -xu

# ADMIN_ARN is set in the ci node env and should not be included in this deploy script

# variables that will likely be changed frequently
CALCLOUD_VER="0.4.30-rc11"
CALDP_VER="v0.2.15-rc3"
CAL_BASE_IMAGE="stsci/hst-pipeline:CALDP_drizzlecats_CAL_rc5"

# this is the tag that the image will have in AWS ECR
CALDP_IMAGE_TAG="latest"

# these variables are overrides for developers that allow the deploy script to build from local calcloud/caldp source
# i.e. CALCLOUD_BUILD_DIR="$HOME/deployer/calcloud"
# these can be set as environment variables before running to avoid changing the script directly
# (and avoid accidentally committing a custom path to the repo...)
CALCLOUD_BUILD_DIR=${CALCLOUD_BUILD_DIR:-""} 
CALDP_BUILD_DIR=${CALDP_BUILD_DIR:-""}
aws_env=${aws_env:-""}

# turn CAL_BASE_IMAGE into CSYS_VER by splitting at the :, splitting again by underscore and keeping the
# first two fields, and then converting to lowercase
CSYS_VER=${CAL_BASE_IMAGE##*:}
CSYS_VER=`echo $CSYS_VER | cut -f1,2 -d'_'` #split by underscores, keep the first two
CSYS_VER=`echo $CSYS_VER | awk '{print tolower($0)}'`

# variables that will be changed less-frequently
TMP_INSTALL_DIR="/tmp/calcloud_install"

# setting up the calcloud source dir if it needs downloaded
# equivalent to "if len($var) == 0"
if [ -z "${CALCLOUD_BUILD_DIR}" ]
then
    mkdir -p $TMP_INSTALL_DIR
    CALCLOUD_BUILD_DIR="${TMP_INSTALL_DIR}/calcloud"
    # calcloud source download/unpack
    cd $TMP_INSTALL_DIR
    git clone https://github.com/spacetelescope/calcloud.git
    cd calcloud && git fetch --all --tags && git checkout tags/v${CALCLOUD_VER} && cd ..
    git_exit_status=$?
    if [[ $git_exit_status -ne 0 ]]; then
        # try without the v
        cd calcloud && git fetch --all --tags && git checkout tags/${CALCLOUD_VER} && cd ..
        git_exit_status=$?
    fi
    if [[ $git_exit_status -ne 0 ]]; then
        echo "could not checkout ${CALCLOUD_VER}; exiting"
        exit 1
    fi
fi

# setting up the caldp source dir if it needs downloaded
# equivalent to "if len($var) == 0"
if [ -z "${CALDP_BUILD_DIR}" ]
then
    mkdir -p $TMP_INSTALL_DIR
    CALDP_BUILD_DIR="${TMP_INSTALL_DIR}/caldp"
    cd $TMP_INSTALL_DIR
    # caldp source download/unpack
    # github's tarballs don't work with pip install, so we have to clone and checkout the tag
    git clone https://github.com/spacetelescope/caldp.git
    cd caldp && git fetch --all --tags && git checkout tags/v${CALDP_VER} && cd ..
    git_exit_status=$?
    if [[ $git_exit_status -ne 0 ]]; then
        # try without the v
        cd caldp && git fetch --all --tags && git checkout tags/${CALDP_VER} && cd ..
        git_exit_status=$?
    fi
    if [[ $git_exit_status -ne 0 ]]; then
        echo "could not checkout ${CALDP_VER}; exiting"
        exit 1
    fi
fi

# get a couple of things from AWS ssm
# the env, i.e. sb,dev,test,prod
if [ -z "${aws_env}" ]
then
    aws_env_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "environment" | grep "Value"`
    aws_env=${aws_env_response##*:}
    aws_env=`echo $aws_env | tr -d '",'`
fi

# the tf state bucket name
aws_tfstate_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "/s3/tfstate" | grep "Value"`
aws_tfstate=${aws_tfstate_response##*:}
aws_tfstate=`echo $aws_tfstate | tr -d '",'`
echo $aws_tfstate

# get AMI id
cd $CALCLOUD_BUILD_DIR/ami_rotation
ami_json=$(echo $(awsudo $ADMIN_ARN aws ec2 describe-images --region us-east-1 --executable-users self))
ci_ami=`python3 parse_image_json.py "${ami_json}" STSCI-AWS-Linux-2`
ecs_ami=`python3 parse_image_json.py "${ami_json}" STSCI-HST-REPRO-ECS`

if [[ "$ci_ami" =~ ^ami-[a-z0-9]+$ ]]; then
    echo $ci_ami
else
    echo "failed to retrieve valid ami id for ci_ami"
    exit 1
fi

if [[ "$ecs_ami" =~ ^ami-[a-z0-9]+$ ]]; then
    echo $ecs_ami
else
    echo "failed to retrieve valid ami id for ecs_ami"
    exit 1
fi

# initial terraform setup
cd ${CALCLOUD_BUILD_DIR}/terraform

# terraform init and s3 state backend config
awsudo $ADMIN_ARN terraform init -backend-config="bucket=${aws_tfstate}" -backend-config="key=calcloud/${aws_env}.tfstate" -backend-config="region=us-east-1"
# deploy ecr
awsudo $ADMIN_ARN terraform plan -var "environment=${aws_env}" -var "ci_ami=${ci_ami}" -var "ecs_ami=${ecs_ami}" -out base.out -target aws_ecr_repository.caldp_ecr
awsudo $ADMIN_ARN terraform apply -auto-approve "base.out"
# get repository url from tf state for use in caldp docker install
repo_url_response=`awsudo $ADMIN_ARN terraform state show aws_ecr_repository.caldp_ecr | grep "repository_url"`
repo_url=${repo_url_response##*=}
# removes double quotes from variable
repo_url=`echo $repo_url | tr -d '"'`

##### DOCKER IMAGE BUILDING #########
CALDP_DOCKER_IMAGE="${repo_url}:${CALDP_IMAGE_TAG}"
PREDICT_DOCKER_IMAGE="${repo_url}:predict"
TRAINING_DOCKER_IMAGE="${repo_url}:training"

# need to "log in" to ecr to push or pull the images
awsudo $ADMIN_ARN aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $repo_url

# naming is confusing here but "modeling" directory plus "training" image is correct
cd ${CALCLOUD_BUILD_DIR}/modeling
set -o pipefail && docker build -f Dockerfile -t "${TRAINING_DOCKER_IMAGE}" .
training_docker_build_status=$?
if [[ $training_docker_build_status -ne 0 ]]; then
    echo "training job docker build failed; exiting"
    exit 1
fi

# jobPredict lambda env
cd ${CALCLOUD_BUILD_DIR}/lambda/JobPredict
set -o pipefail && docker build -f Dockerfile -t "${PREDICT_DOCKER_IMAGE}" .
model_docker_build_status=$?
if [[ $model_docker_build_status -ne 0 ]]; then
    echo "predict lambda env docker build failed; exiting"
    exit 1
fi

# caldp image
cd ${CALDP_BUILD_DIR}
set -o pipefail && docker build -f Dockerfile -t "${CALDP_DOCKER_IMAGE}" --build-arg CAL_BASE_IMAGE="${CAL_BASE_IMAGE}"  .
caldp_docker_build_status=$?
if [[ $caldp_docker_build_status -ne 0 ]]; then
    echo "caldp docker build failed; exiting"
    exit 1
fi

docker push ${TRAINING_DOCKER_IMAGE}
docker push ${PREDICT_DOCKER_IMAGE}
docker push ${CALDP_DOCKER_IMAGE}

#### PRIMARY TERRAFORM BUILD #####
cd ${CALCLOUD_BUILD_DIR}/terraform

# must taint the compute env to be safe about launch template handling. see comments in batch.tf
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[0]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[1]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[2]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[3]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.model_compute_env[0]

# manual confirmation required
awsudo $ADMIN_ARN terraform apply -var "awsysver=${CALCLOUD_VER}" -var "awsdpver=${CALDP_VER}" -var "csys_ver=${CSYS_VER}" -var "environment=${aws_env}" -var "ci_ami=${ci_ami}" -var "ecs_ami=${ecs_ami}"

# make sure needed prefixes exist in primary s3 bucket
# pulls the bucket name in from a tag called Name
bucket_url_response=`awsudo $ADMIN_ARN terraform state show aws_s3_bucket.calcloud | grep "Name"`
bucket_url=${bucket_url_response##*=}
# removes double quotes from variable
bucket_url=`echo $bucket_url | tr -d '"'`

# get the crds context
crds_response=`awsudo $ADMIN_ARN terraform output | grep "crds"`
crds_context=${crds_response##*=}
crds_context=`echo $crds_context | tr -d '"'`

awsudo $ADMIN_ARN aws s3 rm s3://${bucket_url}/crds_env_vars/ --recursive

awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key messages/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key inputs/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key outputs/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key control/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key blackboard/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key crds_env_vars/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key crds_env_vars/${crds_context}


cd $HOME
rm -rf $TMP_INSTALL_DIR
