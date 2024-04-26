#! /bin/bash -xu

# ADMIN_ARN is set in the ci node env and should not be included in this deploy script

source deploy_vars.sh

source deploy_checkout_repos.sh

# the tf state bucket name
aws_tfstate_response=`awsudo $ADMIN_ARN aws ssm get-parameter --name "/s3/tfstate" | grep "Value"`
aws_tfstate=${aws_tfstate_response##*:}
aws_tfstate=`echo $aws_tfstate | tr -d '",'`
echo $aws_tfstate

# get AMI id(s)
cd $CALCLOUD_BUILD_DIR/ami_rotation
ami_json=$(echo $(awsudo $ADMIN_ARN aws ec2 describe-images --region us-east-1 --executable-users self))
ci_ami=`python3 parse_image_json.py "${ami_json}" STSCI-AWS-Linux-2`
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

env | sort

# initial terraform setup
cd ${CALCLOUD_BUILD_DIR}/terraform

awsudo $ADMIN_ARN terraform init -backend-config="bucket=${aws_tfstate}" -backend-config="key=calcloud/${aws_env}.tfstate" -backend-config="region=us-east-1"

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
awsudo $ADMIN_ARN terraform apply -var "awsysver=${CALCLOUD_VER}" -var "awsdpver=${CALDP_VER}" -var "csys_ver=${CSYS_VER}" -var "environment=${aws_env}" -var "ci_ami=${ci_ami}" -var "ecs_ami=${ecs_ami}" -var "full_base_image=${BASE_IMAGE_TAG}" -var "ami_rotation_base_image=${AMIROTATION_DOCKER_IMAGE}"

# brief testing indicates that terraform apply exits with 0 status only if you say yes and the apply succeeds
apply_status=$?
if [[ $apply_status -ne 0 ]]; then
    echo "terraform apply cancelled or failed; exiting deploy"
    exit 1
fi

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

# tag images as in-use by this environment
cd $CALCLOUD_BUILD_DIR/terraform 
# this script doesn't replace "old-tag", it just takes that image, and adds this tag to it. 
# And in fact, if another image exists with this tag, it's removed from that one; so this is image promotion all-in-one
echo ${aws_env}
./deploy_image_promote.sh --old-tag $CALDP_ECR_TAG batch-${aws_env}
./deploy_image_promote.sh --old-tag $PREDICT_ECR_TAG predict-${aws_env}
./deploy_image_promote.sh --old-tag $TRAINING_ECR_TAG training-${aws_env}
./deploy_image_promote.sh --old-tag $AMIROTATION_ECR_TAG amirotation-${aws_env}

cd ${CALCLOUD_BUILD_DIR}/terraform
source deploy_cleanup.sh
