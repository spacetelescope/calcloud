#! /bin/bash -xu

# ADMIN_ARN is set in the ci node env and should not be included in this deploy script

# variables that will likely be changed frequently
CALCLOUD_VER="0.4.8"
CALDP_VER="0.2.7"
CAL_BASE_IMAGE="stsci/hst-pipeline:CALDP_20210323_CAL_final"

# this is the tag that the image will have in AWS ECR
CALDP_IMAGE_TAG="latest"

# turn CAL_BASE_IMAGE into CSYS_VER by splitting at the :, splitting again by underscore and keeping the
# first two fields, and then converting to lowercase
CSYS_VER=${CAL_BASE_IMAGE##*:}
CSYS_VER=`echo $CSYS_VER | cut -f1,2 -d'_'` #split by underscores, keep the first two
CSYS_VER=`echo $CSYS_VER | awk '{print tolower($0)}'`

# variables that will be changed less-frequently
TMP_INSTALL_DIR="/tmp/calcloud_install"

mkdir $TMP_INSTALL_DIR
cd $TMP_INSTALL_DIR

# calcloud source download/unpack
wget "https://github.com/spacetelescope/calcloud/archive/v$CALCLOUD_VER.tar.gz"
tar -xvzf "v$CALCLOUD_VER.tar.gz"
rm "v$CALCLOUD_VER.tar.gz"

# caldp source download/unpack
# github's tarballs don't work with pip install, so we have to clone and checkout the tag
git clone https://github.com/spacetelescope/caldp.git
cd caldp && git fetch --all --tags && git checkout tags/v${CALDP_VER} && cd ..

# get a couple of things from AWS ssm
# the env, i.e. sb,dev,test,prod
aws_env_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "environment" | grep "Value"`
aws_env=${aws_env_response##*:}
aws_env=`echo $aws_env | tr -d '",'`
# the tf state bucket name
aws_tfstate_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "/s3/tfstate" | grep "Value"`
aws_tfstate=${aws_tfstate_response##*:}
aws_tfstate=`echo $aws_tfstate | tr -d '",'`
echo $aws_tfstate

# initial terraform setup
cd calcloud-${CALCLOUD_VER}/terraform

# terraform init and s3 state backend config
awsudo $ADMIN_ARN terraform init -backend-config="bucket=${aws_tfstate}" -backend-config="key=calcloud/${aws_env}.tfstate" -backend-config="region=us-east-1"
# deploy ecr
awsudo $ADMIN_ARN terraform plan -out base.out -target aws_ecr_repository.caldp_ecr
awsudo $ADMIN_ARN terraform apply -auto-approve "base.out"
# get repository url from tf state for use in caldp docker install
repo_url_response=`awsudo $ADMIN_ARN terraform state show aws_ecr_repository.caldp_ecr | grep "repository_url"`
repo_url=${repo_url_response##*=}
# removes double quotes from variable
repo_url=`echo $repo_url | tr -d '"'`

# build and deploy caldp docker image
cd ../../caldp
# cd ~/bhayden/caldp
CALDP_DOCKER_IMAGE="${repo_url}:${CALDP_IMAGE_TAG}"
docker build -f Dockerfile -t ${CALDP_DOCKER_IMAGE} --build-arg CAL_BASE_IMAGE=${CAL_BASE_IMAGE}  .
# need to "log in" to ecr to push the image
awsudo $ADMIN_ARN aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $repo_url
docker push ${CALDP_DOCKER_IMAGE}

# deploy rest of terraform
cd ../calcloud-${CALCLOUD_VER}/terraform
# must taint the compute env to be safe about launch template handling. see comments in batch.tf
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[0]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[1]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[2]
awsudo $ADMIN_ARN terraform taint aws_batch_compute_environment.compute_env[3]

awsudo $ADMIN_ARN terraform taint docker_registry_image.calcloud_predict_model
awsudo $ADMIN_ARN terraform taint module.lambda_function_container_image.aws_lambda_function.this[0]

# manual confirmation required
awsudo $ADMIN_ARN terraform apply -var "awsysver=${CALCLOUD_VER}" -var "awsdpver=${CALDP_VER}" -var "csys_ver=${CSYS_VER}"

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

awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key messages/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key inputs/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key outputs/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key control/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key blackboard/
awsudo $ADMIN_ARN aws s3api put-object --bucket $bucket_url --key crds_env_vars/${crds_context}

cd $HOME
rm -rf $TMP_INSTALL_DIR
