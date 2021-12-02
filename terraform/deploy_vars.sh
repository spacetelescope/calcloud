export CALCLOUD_VER="v0.4.31"
export CALDP_VER="v0.2.16"
export CAL_BASE_IMAGE="stsci/hst-pipeline:CALDP_20211129_CAL_final"

# these variables are overrides for developers that allow the deploy script to build from local calcloud/caldp source
# i.e. CALCLOUD_BUILD_DIR="$HOME/deployer/calcloud"
# these can be set as environment variables before running to avoid changing the script directly
# (and avoid accidentally committing a custom path to the repo...)
export CALCLOUD_BUILD_DIR=${CALCLOUD_BUILD_DIR:-""} 
export CALDP_BUILD_DIR=${CALDP_BUILD_DIR:-""}

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

# turn CAL_BASE_IMAGE into CSYS_VER by splitting at the :, splitting again by underscore and keeping the
# first two fields, and then converting to lowercase
CSYS_VER=${CAL_BASE_IMAGE##*:}
CSYS_VER=`echo $CSYS_VER | cut -f1,2 -d'_'` #split by underscores, keep the first two
export CSYS_VER=`echo $CSYS_VER | awk '{print tolower($0)}'`

# get repo_url here for the central ecr repo