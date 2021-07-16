#! /bin/bash -xu

# ADMIN_ARN is set in the ci node env and should not be included in this deploy script

# variables that will likely be changed frequently
CALCLOUD_VER="0.4.23-rc1"
CALDP_VER="0.2.13-rc1"
CAL_BASE_IMAGE="stsci/hst-pipeline:CALDP_acsflash_dark_wfc3ir_CAL_rc1"

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
fi

# setting up the caldp source dir if it needs downloaded
# equivalent to "if len($var) == 0"
if [ -z "${CALDP_BUILD_DIR}"]
then
    mkdir -p $TMP_INSTALL_DIR
    CALDP_BUILD_DIR="${TMP_INSTALL_DIR}/caldp"
    cd $TMP_INSTALL_DIR
    # caldp source download/unpack
    # github's tarballs don't work with pip install, so we have to clone and checkout the tag
    git clone https://github.com/spacetelescope/caldp.git
    cd caldp && git fetch --all --tags && git checkout tags/v${CALDP_VER} && cd ..
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

# initial terraform setup
cd ${CALCLOUD_BUILD_DIR}/terraform

# terraform init and s3 state backend config
awsudo $ADMIN_ARN terraform init -backend-config="bucket=${aws_tfstate}" -backend-config="key=calcloud/${aws_env}.tfstate" -backend-config="region=us-east-1"

# in order to rotate the ami, requires a new version of the launch template and the associated compute environments
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[0]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[1]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[2]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[3]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.model_compute_env[0]

awsudo $ADMIN_ARN terraform plan -var "environment=${aws_env}" -out ami_rotate.out \
    -target aws_batch_compute_environment.model_compute_env \
    -target aws_batch_compute_environment.compute_env \
    -target aws_batch_job_queue.batch_queue \
    -target aws_batch_job_queue.model_queue \
    -target aws_launch_template.hstdp

awsudo $ADMIN_ARN terraform apply -auto-approve "ami_rotate.out"
