provider "aws" {
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}

module "lambda_function" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "calcloud-job-submit-${var.environment}"
  description   = "looks for placed-ipppssoot messages and submits jobs to Batch"
  # the path is relative to the path inside the lambda env, not in the local filesystem. 
  handler       = "handler.lambda_handler"
  runtime       = "python3.6"
  publish       = true
  timeout       = 30

  source_path = [
    {
      # this is the lambda itself. The code in src will be placed directly into the lambda execution path
      path = "${path.module}/src"
      pip_requirements = false
    },
    {
      # calcloud for the package. We don't need to install boto3 and whatnot so we leave out the pip requirements
      # in the zip it will be installed into a directory called calcloud
      path = "${path.module}/../calcloud/calcloud"
      prefix_in_zip = "calcloud"
      pip_requirements = false
    }
  ]

  store_on_s3 = true
  s3_bucket   = module.s3_bucket.this_s3_bucket_id

  # ensures that terraform doesn't try to mess with IAM
  create_role = false
  attach_cloudwatch_logs_policy = false
  attach_dead_letter_policy = false
  attach_network_policy = false
  attach_tracing_policy = false
  attach_async_event_policy = false
  # existing role for the lambda
  lambda_role = "arn:aws:iam::218835028644:role/bhayden-lambda-role"

  environment_variables = {
    Serverless = "Terraform"
  }

  tags = {
    Name = "calcloud-job-submit-${var.environment}"
  }
}

module "s3_bucket" {
  source = "terraform-aws-modules/s3-bucket/aws"

  bucket        = "calcloud-lambda-envs-${var.environment}"
  force_destroy = true
}

# the next objects set up the lambda to run on a schedule
resource "aws_cloudwatch_event_rule" "every_five_minutes" {
  name                = "calcloud-lambda-submit-${var.environment}"
  description         = "Fires every five minutes"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_cloudwatch_event_target" "check_foo_every_one_minute" {
  rule      = "${aws_cloudwatch_event_rule.every_five_minutes.name}"
  target_id = "${module.lambda_function.this_lambda_function_name}"
  arn       = "${module.lambda_function.this_lambda_function_arn}"
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_check_foo" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = "${module.lambda_function.this_lambda_function_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.every_five_minutes.arn}"
}