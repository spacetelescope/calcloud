#! /bin/bash -xu

source deploy_vars.sh

# Tags an image in ECR by updating the manifest.
# image-promote --old-tag latest-dev latest-test
# image-promote --registry 1234567 --repo myrepo --old-tag latest-dev latest-test

usage() {
    echo "usage: deploy_image_promote.sh [--registry <id>] [--repo <name>] --old-tag <existing-tag> <new-tag>"
    echo
    echo "Adds <new-tag> to the image currently tagged <existing-tag>."
    echo "If another image already has <new-tag>, the tag is moved to this image."
}

registry=$ECR_ACCOUNT_ID
repo=$IMAGE_REPO
old_tag=""

while [ "${1:-}" != "" ]; do
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

if [ -z "$old_tag" ] || [ -z "${1:-}" ]; then
    echo "deploy_image_promote.sh: --old-tag and <new-tag> are both required"
    usage
    exit 2
fi

registry=$registry repo=$repo old_tag=$old_tag new_tag=$1 AWS_PROFILE=hst_reprocessing_admin_role ./deploy_ecr_apply_tag.sh
