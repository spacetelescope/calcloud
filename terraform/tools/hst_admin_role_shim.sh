#/bin/bash
# This script assumes the hst_reprocessing_admin_role, runs a given command using that role, and then switches back to original role

# Set region
export AWS_DEFAULT_REGION="us-east-1"

# Role to assume
ACCOUNT_ID=`aws sts get-caller-identity --output=text | awk '{ print $1 }'`
HST_ADMIN_ARN="arn:aws:iam::${ACCOUNT_ID}:role/hst_reprocessing_admin_role"

# Grab parameters
COMMAND_TO_RUN=$*

# Save current AWS credentials
CURRENT_AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID
CURRENT_AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY
CURRENT_AWS_SESSION_TOKEN=$AWS_SESSION_TOKEN

#Assume role, run command, and switch back
printf "\n Assuming role..."
if CREDENTIALS=`aws sts assume-role --role-arn $HST_ADMIN_ARN --role-session-name temp_admin_session --duration-seconds 3599` ; then

        export AWS_ACCESS_KEY_ID=`echo ${CREDENTIALS} | python -c "import sys, json, os; temp=json.load(sys.stdin)['Credentials']['AccessKeyId'];print(temp)"`
        export AWS_SECRET_ACCESS_KEY=`echo ${CREDENTIALS} | python -c "import sys, json, os; temp=json.load(sys.stdin)['Credentials']['SecretAccessKey'];print(temp)"`
        export AWS_SESSION_TOKEN=`echo ${CREDENTIALS} | python -c "import sys, json, os; temp=json.load(sys.stdin)['Credentials']['SessionToken'];print(temp)"`

        printf "\n Role assumed:"
        aws sts get-caller-identity

        printf "\n Running command\n"
        $COMMAND_TO_RUN

        printf "\n Switching back to original role"
        export AWS_ACCESS_KEY_ID=$CURRENT_AWS_ACCESS_KEY_ID
        export AWS_SECRET_ACCESS_KEY=$CURRENT_AWS_SECRET_ACCESS_KEY
        export AWS_SESSION_TOKEN=$CURRENT_AWS_SESSION_TOKEN

        printf "\n Role switched back:"
        aws sts get-caller-identity

else
        printf "\n==========================\n\n - Error assuming role. Aborting execution\n\n"
        exit 1
fi