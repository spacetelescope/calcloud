module "calcloud_lambda_batchEvents" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 6.0.0"

  function_name = "calcloud-job-events${local.environment}"
  description   = "listens for Batch failure events from cloudWatch event rule"
  # the path is relative to the path inside the lambda env, not in the local filesystem.
  handler       = "batch_event_handler.lambda_handler"
  runtime       = "python3.11"
  publish       = false
  timeout       = 900
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  source_path = [
    {
      # this is the lambda itself. The code in path will be placed directly into the lambda execution path
      path = "${path.module}/../lambda/batch_events"
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

  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_submit_role.value)

  environment_variables = merge(local.common_env_vars, {
    MAX_MEMORY_RETRIES="4",
    MAX_DOCKER_RETRIES="4"
  })

  tags = {
    Name = "calcloud-job-events${local.environment}"
  }
}

# the event rule for this lambda/cloudwatch interaction is AWS failure events
resource "aws_cloudwatch_event_rule" "batch" {
  name = "capture-batch-failure-events${local.environment}"
  description = "capture AWS Batch failures to send to lambda for evaluation"

  event_pattern = <<EOF
{
  "source": [
    "aws.batch"
  ],
  "detail-type": [
    "Batch Job State Change"
  ],
  "detail": {
    "status": ["FAILED"]
  }
}
EOF
}

resource "aws_cloudwatch_event_target" "batch_events" {
  rule      = aws_cloudwatch_event_rule.batch.name
  target_id = "lambda"
  arn       = module.calcloud_lambda_batchEvents.lambda_function_arn
}

resource "aws_lambda_permission" "allow_lambda_exec_batch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_lambda_batchEvents.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.batch.arn
}
