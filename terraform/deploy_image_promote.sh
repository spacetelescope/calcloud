#! /bin/bash -xu

source deploy_vars.sh

# Tags an image in ECR by updating the manifest.
# image-promote latest-test
# allows you to use args for flexibility which is recommended
# image-promote --registry 1234567 --repo myrepo --old-tag latest-dev latest-test

registry=$ECR_ACCOUNT_ID
repo=$IMAGE_REPO
old_tag=`echo $IMAGE_TAG | sed -e 's/unscanned-//g'`

while [ "$1" != "" ]; do
    case $1 in
        -r | --registry )
            shift
            registry=$1
            ;;
        -i | --repo )
            shift
            repo=$1
            ;;
        -t | --old-tag )
            shift
            old_tag=$1
            ;;
        -h | --help )
            usage
            exit
	    ;;
	* )
	    break  # Default case: no more options so break out and leave remaining args unshifted 
    esac
    shift
done

# This greatly saddens me but this subprogram is the only way to get this working because of two reasons
# awsudo seems to have a bug where it will unquote a quoted variable when it translates the command
# the ecr tag updating process is so finnicky that trying to modify it in any way breaks it
registry=$registry repo=$repo old_tag=$old_tag new_tag=$1 awsudo $ADMIN_ARN ./deploy_ecr_apply_tag.sh
