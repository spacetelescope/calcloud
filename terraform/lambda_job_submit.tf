module "calcloud_lambda_submit" {
  source = "terraform-aws-modules/lambda/aws"
  # https://github.com/hashicorp/terraform/issues/17211
  version = "~> 1.43.0"

  function_name = "calcloud-job-submit${local.environment}"
  description   = "looks for placed-ipppssoot messages and submits jobs to Batch"
  # the path is relative to the path inside the lambda env, not in the local filesystem.
  handler       = "s3_trigger_handler.lambda_handler"
  runtime       = "python3.6"
  publish       = false
  timeout       = 15*60   # see also SUBMIT_TIMEOUT below;  this is the AWS timeout, calcloud error handling may not occur
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  source_path = [
    {
      # this is the lambda itself. The code in path will be placed directly into the lambda execution path
      path = "${path.module}/../lambda/s3_trigger"
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

  environment_variables = merge(local.common_env_vars, {
      JOBPREDICTLAMBDA = module.lambda_function_container_image.this_lambda_function_arn,
      SUBMIT_TIMEOUT = 14*60,  # leave some room for polling jitter, 14 min vs  15 min above
  })                           # this is our timeout so error handling / cleanup should occur

  tags = {
    Name = "calcloud-job-submit${local.environment}"
  }
}

# for the s3 event trigger for submit lambda
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_lambda_submit.this_lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.calcloud.arn
}
