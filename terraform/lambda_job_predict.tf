module "lambda_function_container_image" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 2.26.0"
  function_name = "calcloud-job-predict${local.environment}"
  description   = "pretrained neural networks for predicting job resource requirements (memory bin and max execution time)"

  create_package = false
  image_uri = local.ecr_predict_lambda_image
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

  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_predict_role.value)

  environment_variables = merge(local.common_env_vars, {
  })

  tags = {
    Name = "calcloud-job-predict${local.environment}"
  }
}
