module "calcloud_lambda_rescueJob" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 2.26.0"

  function_name = "calcloud-job-rescue${local.environment}"
  description   = "Rescues the specified dataset (must be in error state) by deleting all outputs and messages and re-placing."
  # the path is relative to the path inside the lambda env, not in the local filesystem.
  handler       = "rescue_handler.lambda_handler"
  runtime       = "python3.7"
  publish       = false
  timeout       = 900
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  source_path = [
    {
      # this is the lambda itself. The code in path will be placed directly into the lambda execution path
      path = "${path.module}/../lambda/JobRescue"
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

  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_rescue_role.value)

  environment_variables = merge(local.common_env_vars, {
      JOBPREDICTLAMBDA = module.lambda_function_container_image.lambda_function_arn,
      SUBMIT_TIMEOUT = 14*60,  # leave some room for polling jitter, 14 min vs  15 min above
      DDBTABLE = "${aws_dynamodb_table.calcloud_model_db.name}"
  })   

  tags = {
    Name = "calcloud-job-rescue${local.environment}"
  }
}

# for the s3 event trigger for rescue lambda
resource "aws_lambda_permission" "allow_bucket_rescueLambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_lambda_rescueJob.lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.calcloud.arn
  source_account = data.aws_caller_identity.this.account_id
}
