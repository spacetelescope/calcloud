module "calcloud_lambda_cleanJob" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 1.43.0"

  function_name = "calcloud-job-clean${local.environment}"
  description   = "accepts messages from s3 event and cleans either individual jobs by ipppssoot, or all active jobs"
  # the path is relative to the path inside the lambda env, not in the local filesystem.
  handler       = "clean_handler.lambda_handler"
  runtime       = "python3.6"
  publish       = false
  timeout       = 900
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  source_path = [
    {
      # this is the lambda itself. The code in path will be placed directly into the lambda execution path
      path = "${path.module}/../lambda/JobClean"
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
  lambda_role = data.aws_ssm_parameter.lambda_cleanup_role.value

  environment_variables = merge(local.common_env_vars, {
  })

  tags = {
    Name = "calcloud-job-clean${local.environment}"
  }
}

# for the s3 event trigger for clean lambda
resource "aws_lambda_permission" "allow_bucket_cleanLambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_lambda_cleanJob.this_lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.calcloud.arn
}
