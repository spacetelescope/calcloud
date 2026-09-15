#! /bin/bash -xu

# checks if image tag(s) exist; exit 1 if so
# used in deploy.sh to avoid accidentally re-pushing an image that already exists.

source deploy_vars.sh

TAGS=$*

if [[ "$#" == "0" ]]; then
    echo "usage: deploy_check_existing_imageTag.sh <tag1 tag2 tag3 ...>"
    echo
    exit 2
fi

anyImage="0"
for imageTag in ${TAGS}; do
    # describe images returns exit code 1 if the image does not exist
    # batch-get-image does NOT
    describe_output=$(AWS_PROFILE=hst_reprocessing_admin_role aws ecr describe-images --registry-id ${ECR_ACCOUNT_ID} --repository-name ${IMAGE_REPO} --image-ids imageTag=${imageTag} 2>&1)
    describe_status=$?

    if [[ $describe_status -eq 0 ]]; then
        echo "${imageTag} already exists."
        anyImage="1"
    elif [[ "${describe_output}" == *"ImageNotFoundException"* ]]; then
        : # expected for tags which do not exist yet
    else
        echo "${describe_output}" >&2
        exit ${describe_status}
    fi
done 

if [[ $anyImage -eq "1" ]]; then
    exit 1
fi
