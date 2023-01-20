#! /bin/bash -xu

export CALCLOUD_VER="v0.4.39-rc2"
export CALDP_VER="v0.2.21-rc2"
export CAL_BASE_IMAGE="stsci/hst-pipeline:CALDP_drizcosstis_CAL_rc2"

export BASE_IMAGE_TAG=`cut -d ":" -f2- <<< ${CAL_BASE_IMAGE} `

export COMMON_IMAGE_TAG="CALCLOUD_${CALCLOUD_VER}-CALDP_${CALDP_VER}-BASE_${BASE_IMAGE_TAG}"
# these variables are overrides for developers that allow the deploy script to build from local calcloud/caldp source
# i.e. CALCLOUD_BUILD_DIR="$HOME/deployer/calcloud"
# these can be set as environment variables before running to avoid changing the script directly
# (and avoid accidentally committing a custom path to the repo...)
export CALCLOUD_BUILD_DIR=${CALCLOUD_BUILD_DIR:-""}
export CALDP_BUILD_DIR=${CALDP_BUILD_DIR:-""}

export TMP_INSTALL_DIR="/tmp/calcloud_install"

# get a couple of things from AWS ssm
# the env, i.e. sb,dev,test,prod
aws_env=${aws_env:-""}
if [ -z "${aws_env}" ]
then
    aws_env_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "environment" | grep "Value"`
    aws_env=${aws_env_response##*:}
    aws_env=`echo $aws_env | tr -d '",'`
fi
export aws_env=${aws_env}

# the central ecr url
repo_url=${repo_url:-""}
if [ -z "${repo_url}" ]
then
    repo_url_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "/ecr/SharedServices" | grep "Value"`
    repo_url=${repo_url_response##*:}
    repo_url=`echo $repo_url | tr -d '",'`
fi
export repo_url=${repo_url}
export ECR_ACCOUNT_ID=`echo $repo_url | cut -d '.' -f1`    # 378083651696
export IMAGE_REPO=`echo $repo_url | cut -d '/' -f2`        # hst-repro

##### DOCKER IMAGE BUILDING #########
# tags are exported individually for some ecr api call convenience in other scripts
export CALDP_ECR_TAG="batch-${COMMON_IMAGE_TAG}"
export PREDICT_ECR_TAG="predict-${COMMON_IMAGE_TAG}"
export TRAINING_ECR_TAG="training-${COMMON_IMAGE_TAG}"

export CALDP_DOCKER_IMAGE="${repo_url}:${CALDP_ECR_TAG}"
export PREDICT_DOCKER_IMAGE="${repo_url}:${PREDICT_ECR_TAG}"
export TRAINING_DOCKER_IMAGE="${repo_url}:${TRAINING_ECR_TAG}"

# turn CAL_BASE_IMAGE into CSYS_VER by splitting at the :, splitting again by underscore and keeping the
# first two fields, and then converting to lowercase
CSYS_VER=${CAL_BASE_IMAGE##*:}
CSYS_VER=`echo $CSYS_VER | cut -f1,2 -d'_'` #split by underscores, keep the first two
export CSYS_VER=`echo $CSYS_VER | awk '{print tolower($0)}'`

# get repo_url here for the central ecr repo
