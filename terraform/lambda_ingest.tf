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

  environment_variables = {BUCKET = "calcloud-processing${local.environment}"}

  tags = {
    Name = "calcloud-lambda-scrape${local.environment}"
  }
}

resource "aws_s3_bucket_notification" "trigger_ingest" {
    bucket = aws_s3_bucket.calcloud.id

    lambda_function {
        lambda_function_arn = module.calcloud_lambda_ingest.aws_lambda_function.arn
        events              = ["s3:ObjectCreated:*"]
        filter_prefix       = "messages/processed-"
        filter_suffix       = ".trigger"
    }
}