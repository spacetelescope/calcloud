module "calcloud_lambda_refresh_cache_submit" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 2.26.0"

  function_name = "calcloud-fileshare-refresh_cache_submit${local.environment}"
  description   = "submits refresh cache operations"
  # the path is relative to the path inside the lambda env, not in the local filesystem.
  handler       = "refresh_cache_submit.lambda_handler"
  runtime       = "python3.11"
  publish       = false
  timeout       = 900
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  source_path = [
    {
      # this is the lambda itself. The code in path will be placed directly into the lambda execution path
      path = "${path.module}/../lambda/refreshCacheSubmit"
      pip_requirements = false
    },
    {
      # calcloud for the package. We don't need to install boto3 and whatnot so we leave out the pip requirements
      # in the zip it will be installed into a directory called calcloud
      path = "${path.module}/../calcloud"
      prefix_in_zip = "calcloud"
      pip_requirements = false
    },
    {
      # pip dependencies defined for calcloud package in requirements.txt
      path = "${path.module}/../calcloud"
      pip_requirements = true
    },
  ]

  store_on_s3 = true
  s3_bucket   = aws_s3_bucket.calcloud_lambda_envs.id

  # ensures that terraform doesn't try to mess with IAM
  create_role = false
  attach_cloudwatch_logs_policy = false
  attach_dead_letter_policy = false
  attach_network_policy = false
  attach_tracing_policy = false
  attach_async_event_policy = false

  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_refreshCacheSubmit_role.value)

  environment_variables = merge(local.common_env_vars, {
    FS_BLACKBOARD = nonsensitive(data.aws_ssm_parameter.fs_blackboard_arn.value),
    FS_CONTROL = nonsensitive(data.aws_ssm_parameter.fs_control_arn.value),
    FS_CRDS = nonsensitive(data.aws_ssm_parameter.fs_crds_arn.value),
    FS_INPUTS = nonsensitive(data.aws_ssm_parameter.fs_inputs_arn.value),
    FS_MESSAGES = nonsensitive(data.aws_ssm_parameter.fs_messages_arn.value),
    FS_OUTPUTS = nonsensitive(data.aws_ssm_parameter.fs_outputs_arn.value)
  })

  tags = {
    Name = "calcloud-fileshare-refresh_cache_submits${local.environment}"
  }
}

resource "aws_cloudwatch_event_rule" "refresh_cache_schedule" {
  name                = "refresh-cache-scheduler${local.environment}"
  description         = "refreshes all file share caches"
  schedule_expression = "rate(9 minutes)"
}

resource "aws_cloudwatch_event_target" "refresh_cache_submit" {
  rule      = aws_cloudwatch_event_rule.refresh_cache_schedule.name
  target_id = "lambda"
  arn       = module.calcloud_lambda_refresh_cache_submit.lambda_function_arn
}

resource "aws_lambda_permission" "refresh_cache_submit" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_lambda_refresh_cache_submit.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.refresh_cache_schedule.arn
}
