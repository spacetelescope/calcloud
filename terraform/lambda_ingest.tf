module "calcloud_lambda_ingest" {
  source = "terraform-aws-modules/lambda/aws"
  function_name = "calcloud-ingest${local.environment}"
  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_predict_role.value)
  description   = "looks for processed-ipppssoot.trigger messages, scrapes and uploads completed job data to DynamoDB"
  handler       = "lambda_scrape.lambda_handler"
  runtime       = "python3.8"
  create_package       = false
  timeout       = 180
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days
  s3_existing_package = {
    bucket = "calcloud-modeling${local.environment}"
    key = "lambda/calcloud-ingest.zip"
  }
  create_role = false
  attach_cloudwatch_logs_policy = false
  attach_dead_letter_policy = false
  attach_network_policy = false
  attach_tracing_policy = false
  attach_async_event_policy = false

  allowed_triggers = {
    S3TriggerMessage = {
      principal = "s3.amazonaws.com"
      source_arn = "arn:aws:s3:${data.aws_region.current.name}:${data.aws_caller_identity.this.account_id}:${aws_s3_bucket.calcloud.id}"
    }
  }

  tags = {
    Name = "calcloud-lambda-ingest${local.environment}"
  }
}

resource "aws_s3_bucket_notification" "trigger_ingest" {
    bucket = "calcloud-processing${local.environment}"

    lambda_function {
        lambda_function_arn = module.calcloud_lambda_ingest.this_lambda_function_arn
        events              = ["s3:ObjectCreated:*"]
        filter_prefix       = "messages/processed-"
        filter_suffix       = ".trigger"
    }
}