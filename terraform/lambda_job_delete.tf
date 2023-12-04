module "calcloud_lambda_deleteJob" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 6.0.0"

  function_name = "calcloud-job-delete${local.environment}"
  description   = "accepts messages from s3 event and deletes either individual jobs by dataset, or all active jobs"
  # the path is relative to the path inside the lambda env, not in the local filesystem.
  handler       = "delete_handler.lambda_handler"
  runtime       = "python3.11"
  publish       = false
  timeout       = 900
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  source_path = [
    {
      # this is the lambda itself. The code in path will be placed directly into the lambda execution path
      path = "${path.module}/../lambda/JobDelete"
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

  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_delete_role.value)

  environment_variables = merge(local.common_env_vars, {
  })

  tags = {
    Name = "calcloud-job-delete${local.environment}"
  }
}

# for the s3 event trigger for delete lambda
resource "aws_lambda_permission" "allow_bucket_deleteLambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_lambda_deleteJob.lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.calcloud.arn
  source_account = data.aws_caller_identity.this.account_id
}
