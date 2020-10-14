This set of terraform scripts will stand up an AWS Batch processing environment to process *HST* data using a docker image.

### Prerequisites
- terraform
- docker
- a functioning AWS CLI environment
- a python environment with `caldp` installed: https://github.com/spacetelescope/caldp

### Instructions
- in `batch.tf`, in the provider object at the top, insert the name of your AWS account from your credentials file
- in your AWS account you will need a keypair.
- make a file in this directory called `local.tfvars` and assign the `image_tag` and `keypair` variables. `image_tag = "latest"` should work if you don't change any defaults anywhere. The `keypair` is whatever you created above. 
- first, we need to stand up the ECR so we have a place to push our docker image
    - `terraform plan -out base.out -target aws_ecr_repository.caldp_ecr -var-file local.tfvars`
    - `terraform apply "base.out"`
- now, go to your `caldp` python environment. Modify `scripts/caldp-image-config`, changing the line starting with `export CALDP_IMAGE_REPO=` to reference the ARN of the ECR created by terraform. You can get this through the AWS ECR console, or by running `terraform show`. It is the `repository_url` in the `terraform show` output. *MAKE SURE TO RERUN `pip install .` IF YOU CHANGE THE SCRIPT AND ARE RUNNING THE SCRIPTS AS EXECUTABLES IN YOUR PATH*
- run `caldp-image-build`
- run `caldp-image-push`
    -*note: you may get an error about needing to login. If so, run the following command:*
    `aws ecr get-login-password --region your-region-here | docker login --username AWS your:ecr:arn:goes/here`
- now apply the rest of the terraform stack
    - `terraform plan -var-file=local.tfvars`
    - `terraform apply`

Now you should have a functioning AWS Batch environment that can run the caldp docker image. To destroy it just run `terraform destroy -var-file=local.tfvars`