#! /bin/bash -xu

IMAGES=$*

if [[ "$#" == "0" ]]; then
    echo "usage: deploy_ecr_image_delete.sh  <tag-or-ecr-digest>..."
    echo
    echo "Removes the specified tags or sha256 digests from ECR."
    echo "Deleting a tag leaves all other references intact.  The image is only deleted when the last tag on"
    echo "  that digest is deleted."
    echo "Deleting a sha256 digest deletes the image and EVERY tag referring to it."
    echo
    echo "e.g. deploy_ecr_image_delete.sh latest                                                                   # tag"
    echo "e.g. deploy_ecr_image_delete.sh sha256:684afe25b7a68e83c7c3758533020ea6736a0e11d63f1dedcf4b761faeca99ab  # sha256 digest"
    exit 2
fi

SSM_PARAM=`awsudo $ADMIN_ARN aws ssm get-parameter --name "/ecr/SharedServices" --query "Parameter.Value" --output text`
ECR_ACCOUNT_ID=`echo $SSM_PARAM | cut -d '.' -f1`    # 123456789123
IMAGE_REPO=`echo $SSM_PARAM | cut -d '/' -f2`        # ecr-repo-name

for image in ${IMAGES}; do
    if [[ `echo $image | cut -d':' -f1` == "sha256" ]]; then
       QUALIFIER=imageDigest
    else
	    QUALIFIER=imageTag
    fi
    awsudo ${ADMIN_ARN} aws ecr batch-delete-image --registry-id ${ECR_ACCOUNT_ID} --repository-name ${IMAGE_REPO} --image-ids ${QUALIFIER}=${image}
done