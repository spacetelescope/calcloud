#! /bin/bash -xu

manifest=$(aws ecr batch-get-image --registry-id $registry --repository-name $repo --image-ids imageTag="$old_tag" --query 'images[].imageManifest' --output text)
get_status=$?
if [ $get_status -ne 0 ] || [ -z "$manifest" ] || [ "$manifest" == "None" ]; then
    echo "Could not find image tagged $old_tag in $repo; tag $new_tag was not applied"
    exit 1
fi

# capture output so the CLI doesn't page the response and wait for user input
put_output=$(aws ecr put-image --registry-id $registry --repository-name $repo --image-tag "$new_tag" --image-manifest "$manifest" --output text 2>&1)
put_status=$?
if [ $put_status -ne 0 ]; then
    if grep -q "ImageAlreadyExistsException" <<< "$put_output"; then
        echo "$new_tag already points to the image tagged $old_tag; nothing to do"
    else
        echo "$put_output"
        echo "Failed to tag image $old_tag as $new_tag in $repo"
        exit 1
    fi
fi
