data "aws_caller_identity" "this" {}
data "aws_region" "current" {}
data "aws_ecr_authorization_token" "token" {}

provider "docker" {
  registry_auth {
    address  = local.ecr_address
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
}

resource "docker_registry_image" "calcloud_predict_model" {
  name = local.ecr_image

  build {
    context = "../lambda/JobPredict"
  }
}

module "lambda_function_container_image" {
  source = "terraform-aws-modules/lambda/aws"
  function_name = "calcloud-job-predict${local.environment}"
  description   = "pretrained neural networks for predicting job resource requirements (memory bin and max execution time)"

  depends_on = [docker_registry_image.calcloud_predict_model]

  create_package = false
  image_uri = docker_registry_image.calcloud_predict_model.name
  package_type = "Image"

  timeout       = 180
  memory_size   = 500
  cloudwatch_logs_retention_in_days = 30

  # ensures that terraform doesn't try to mess with IAM
  create_role = false
  attach_cloudwatch_logs_policy = false
  attach_dead_letter_policy = false
  attach_network_policy = false
  attach_tracing_policy = false
  attach_async_event_policy = false
  # existing role for the lambda
  lambda_role = data.aws_ssm_parameter.lambda_predict_role.value
  #lambda_role = var.lambda_predict_role

  tags = {
    Name = "calcloud-job-predict${local.environment}"
  }
}