resource "aws_lambda_function" "calcloud_ingest" {
  function_name = "calcloud-ingest${local.environment}"
  role = nonsensitive(data.aws_ssm_parameter.lambda_predict_role.value)
  description   = "looks for processed-ipppssoot.trigger messages, scrapes and uploads completed job data to DynamoDB"
  # the path is relative to the path inside the lambda env, not in the local filesystem.
  handler       = "lambda_scrape.lambda_handler"
  runtime       = "python3.8"
  publish       = false
  timeout       = 180   # see also SUBMIT_TIMEOUT below;  this is the AWS timeout, calcloud error handling may not occur
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days
  s3_bucket = "calcloud-modeling${local.environment}"
  s3_key = "lambda/calcloud-ingest.zip"

  # ensures that terraform doesn't try to mess with IAM
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