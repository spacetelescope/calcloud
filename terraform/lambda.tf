module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "calcloud-job-submit${local.environment}"
  description   = "looks for placed-ipppssoot messages and submits jobs to Batch"
  # the path is relative to the path inside the lambda env, not in the local filesystem. 
  handler       = "s3_trigger_handler.lambda_handler"
  runtime       = "python3.6"
  publish       = true
  timeout       = 30

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

  environment_variables = {
    JOBDEFINITION = aws_batch_job_definition.calcloud.name,
    NORMALQUEUE = aws_batch_job_queue.batch_queue.name,
    OUTLIERQUEUE = aws_batch_job_queue.batch_outlier_queue.name,
    S3_PROCESSING_BUCKET = aws_s3_bucket.calcloud.id
  }

  tags = {
    Name = "calcloud-job-submit${local.environment}"
  }
}

resource "aws_s3_bucket" "calcloud_lambda_envs" {
  bucket = "calcloud-lambda-envs${local.environment}"
  tags = {
    "Name"     = "calcloud-lambda-envs${local.environment}"
  }
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "s3_lambda_public_block" {
  bucket = aws_s3_bucket.calcloud_lambda_envs.id

  block_public_acls   = true
  block_public_policy = true
  restrict_public_buckets = true
  ignore_public_acls=true
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_function.this_lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.calcloud.arn
}

resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.calcloud.id

  lambda_function {
    lambda_function_arn = module.lambda_function.this_lambda_function_arn
    events              = ["s3:ObjectCreated:Put"]
    filter_prefix       = "messages/placed-"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}