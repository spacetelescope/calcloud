#! /bin/bash -xu

# ADMIN_ARN is set in the ci node env and should not be included in this deploy script

source deploy_vars.sh

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

#### this section is temporary until we start using the central ecr. It will need to be revised at that point to
# remove terraforming the ecr. Logging in will still be required.
# we'll pull the ecr from ssm, where it's populated by IT's CF templates.
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
export repo_url=${repo_url}

# need to "log in" to ecr to push or pull the images
awsudo $ADMIN_ARN aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $repo_url

# temporary docker builds here until central ecr refactor
# script will not exist for calcloud version <= 0.4.31.
# will need to either set a custom build dir or use a later version of calcloud
cd ${CALCLOUD_BUILD_DIR}/terraform
bash deploy_docker_builds.sh

#### PRIMARY TERRAFORM BUILD #####
cd ${CALCLOUD_BUILD_DIR}/terraform

# must taint the compute env to be safe about launch template handling. see comments in batch.tf
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[0]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[1]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[2]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[3]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.model_compute_env[0]
awsudo $ADMIN_ARN terraform taint module.lambda_function_container_image.aws_lambda_function.this[0]

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
