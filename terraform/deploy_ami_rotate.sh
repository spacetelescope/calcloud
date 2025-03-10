#! /bin/bash -xu

# ADMIN_ARN is set in the ci node env and should not be included in this deploy script
aws_env=${aws_env:-""}

# get the versions from ssm params
calcloud_ver_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "/tf/env/awsysver-${aws_env}" | grep "Value"`
CALCLOUD_VER=${calcloud_ver_response##*:}
CALCLOUD_VER=`echo $CALCLOUD_VER | tr -d '",'`

caldp_ver_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "/tf/env/awsdpver-${aws_env}" | grep "Value"`
CALDP_VER=${caldp_ver_response##*:}
CALDP_VER=`echo $CALDP_VER | tr -d '",'`

csys_ver_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "/tf/env/csys_ver-${aws_env}" | grep "Value"`
CSYS_VER=${csys_ver_response##*:}
CSYS_VER=`echo $CSYS_VER | tr -d '",'`

# these variables are overrides for developers that allow the deploy script to build from local calcloud/caldp source
# i.e. CALCLOUD_BUILD_DIR="$HOME/deployer/calcloud"
# these can be set as environment variables before running to avoid changing the script directly
# (and avoid accidentally committing a custom path to the repo...)
CALCLOUD_BUILD_DIR=${CALCLOUD_BUILD_DIR:-""} 
CALDP_BUILD_DIR=${CALDP_BUILD_DIR:-""}

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

# check for Batch jobs and exit if any exist that are running or should be soon
cd ${CALCLOUD_BUILD_DIR}/scripts
./check_batch_jobs.py 
batch_jobs=$?
if [[ $batch_jobs -ne 0 ]]; then
    echo "there are running or submitted batch jobs; cannot rotate ami"
    exit 1
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
ci_ami=`python3 parse_image_json.py "${ami_json}" STSCI-AMAZON-LINUX2023`
ecs_ami=`python3 parse_image_json.py "${ami_json}" STSCI-ECS-AL2023`

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

# in order to rotate the ami, requires a new version of the launch template and the associated compute environments
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[0]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[1]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[2]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[3]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.model_compute_env[0]

awsudo $ADMIN_ARN terraform plan -no-color -var "environment=${aws_env}" -out ami_rotate.out \
    -target aws_batch_compute_environment.model_compute_env \
    -target aws_batch_compute_environment.compute_env \
    -target aws_batch_job_queue.batch_queue \
    -target aws_batch_job_queue.model_queue \
    -target aws_launch_template.hstdp \
    -target aws_launch_template.ami_rotation \
    -var "awsysver=${CALCLOUD_VER}" -var "awsdpver=${CALDP_VER}" -var "csys_ver=${CSYS_VER}" -var "environment=${aws_env}" -var "ci_ami=${ci_ami}" -var "ecs_ami=${ecs_ami}"

awsudo $ADMIN_ARN terraform apply -no-color "ami_rotate.out"

cd $HOME
rm -rf $TMP_INSTALL_DIR
