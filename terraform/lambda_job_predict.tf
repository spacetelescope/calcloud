data "aws_caller_identity" "this" {}
data "aws_region" "current" {}
data "aws_ecr_authorization_token" "token" {}

provider "docker" {
  registry_auth {
    address  = local.ecr_address
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
  ca_material = pathexpand("../lambda/JobPredict/certs/tls-cs-bundle.pem")
}

resource "docker_registry_image" "calcloud_predict_model" {
  name = local.ecr_predict_lambda_image

  build {
    context = "../lambda/JobPredict"
    no_cache=true
    remove=true
  }
}

module "lambda_function_container_image" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 1.43.0"
  function_name = "calcloud-job-predict${local.environment}"
  description   = "pretrained neural networks for predicting job resource requirements (memory bin and max execution time)"

  depends_on = [docker_registry_image.calcloud_predict_model]

  create_package = false
  image_uri = docker_registry_image.calcloud_predict_model.name
  package_type = "Image"

  timeout       = 360
  memory_size   = 1024
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  # ensures that terraform doesn't try to mess with IAM
  create_role = false
  attach_cloudwatch_logs_policy = false
  attach_dead_letter_policy = false
  attach_network_policy = false
  attach_tracing_policy = false
  attach_async_event_policy = false
  # existing role for the lambda
  lambda_role = data.aws_ssm_parameter.lambda_predict_role.value

  environment_variables = merge(local.common_env_vars, {
  })

  tags = {
    Name = "calcloud-job-predict${local.environment}"
  }
}
