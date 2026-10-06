module "calcloud_lambda_codebuildEvents" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 6.0.0"

  function_name = "calcloud-codebuild-events${local.environment}"
  description   = "sends CodeBuild state change events to Datadog"
  handler       = "codebuild_event_handler.lambda_handler"
  runtime       = "python3.11"
  publish       = false
  timeout       = 60
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  source_path = [
    {
      path = "${path.module}/../lambda/codebuild_events"
      pip_requirements = false
    },
    {
      path = "${path.module}/../calcloud"
      prefix_in_zip = "calcloud"
      pip_requirements = false
    },
  ]

  store_on_s3 = true
  s3_bucket   = aws_s3_bucket.calcloud_lambda_envs.id

  create_role = false
  attach_cloudwatch_logs_policy = false
  attach_dead_letter_policy = false
  attach_network_policy = false
  attach_tracing_policy = false
  attach_async_event_policy = false

  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_submit_role.value)

  environment_variables = merge(local.common_env_vars, {})

  tags = {
    Name              = "calcloud-codebuild-events${local.environment}"
    "stsci-poc-email" = var.stsci_poc_email
  }
}
