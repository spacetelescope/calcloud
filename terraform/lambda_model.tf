module "lambda_function_container_image" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "calcloud-ai"
  description   = "pretrained neural network generates job resource requirement predictions"

  create_package = false

  image_uri    = "218835028644.dkr.ecr.us-east-1.amazonaws.com/calcloud-ai"
  package_type = "Image"
}