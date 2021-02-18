module "calcloud_lambda_batchEvents" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "calcloud-job-events${local.environment}"
  description   = "listens for Batch failure events from cloudWatch event rule"
  # the path is relative to the path inside the lambda env, not in the local filesystem. 
  handler       = "batch_event_handler.lambda_handler"
  runtime       = "python3.6"
  publish       = false
  timeout       = 900

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
    }
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
  # existing role for the lambda
  # will need to parametrize when ITSD takes over role creation. 
  # for now this role was created by hand in the console, it is not terraform managed
  lambda_role = data.aws_ssm_parameter.lambda_submit_role.value

  environment_variables = {
    JOBQUEUES="${aws_batch_job_queue.batch_queue.name},${aws_batch_job_queue.batch_outlier_queue.name}"
  }

  tags = {
    Name = "calcloud-job-events${local.environment}"
  }
}

# the event rule for this lambda/cloudwatch interaction is AWS failure events
resource "aws_cloudwatch_event_rule" "batch" {
  name = "capture-batch-failure-events"
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
  arn       = module.calcloud_lambda_batchEvents.this_lambda_function_arn
}

resource "aws_lambda_permission" "allow_lambda_exec_batch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_lambda_batchEvents.this_lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.batch.arn
}