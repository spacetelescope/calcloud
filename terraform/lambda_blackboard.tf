module "calcloud_lambda_blackboard" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "calcloud-job-blackboard${local.environment}"
  description   = "scrapes the Batch console for job metadata and posts to S3 bucket for on-premise poller"
  # the path is relative to the path inside the lambda env, not in the local filesystem. 
  handler       = "scrape_batch.lambda_handler"
  runtime       = "python3.6"
  publish       = false
  timeout       = 300
  cloudwatch_logs_retention_in_days = 30

  source_path = [
    {
      # this is the lambda itself. The code in path will be placed directly into the lambda execution path
      path = "${path.module}/../lambda/blackboard"
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
  # lambda_role = data.aws_ssm_parameter.lambda_submit_role.value
  lambda_role = data.aws_ssm_parameter.lambda_blackboard_role.value

  environment_variables = {
    # comma delimited list of job queues, because batch can only list jobs per queue
    JOBQUEUES="${aws_batch_job_queue.batch_queue.name},${aws_batch_job_queue.batch_outlier_queue.name}"
    BUCKET=aws_s3_bucket.calcloud.id
    FILESHARE=data.aws_ssm_parameter.file_share_arn.value
  }

  tags = {
    Name = "calcloud-job-blackboard${local.environment}"
  }
}

# for cron-like schedule of blackboard lambda
resource "aws_cloudwatch_event_rule" "every_five_minutes" {
  name                = "every-five-minutes"
  description         = "Fires every five minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "every_five_minutes" {
  rule      = aws_cloudwatch_event_rule.every_five_minutes.name
  target_id = "lambda"
  arn       = module.calcloud_lambda_blackboard.this_lambda_function_arn
}

resource "aws_lambda_permission" "allow_lambda_exec" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_lambda_blackboard.this_lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_five_minutes.arn
}