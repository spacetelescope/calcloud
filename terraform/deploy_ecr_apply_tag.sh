#! /bin/bash -xu

manifest=$(aws ecr batch-get-image --registry-id $registry --repository-name $repo --image-ids imageTag="$old_tag" --query 'images[].imageManifest' --output text)
# I had to route this command to a file to avoid the terminal printing the response and forcing user-input to continue
aws ecr put-image --registry-id $registry --repository-name $repo --image-tag "$new_tag" --image-manifest "$manifest" --output text > dummy.json
rm dummy.json