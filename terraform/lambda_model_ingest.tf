resource "aws_dynamodb_table" "calcloud_model_db" {
  name           = "calcloud-model${local.environment}"
  billing_mode   = "PROVISIONED"
  read_capacity  = 10
  write_capacity = 10
  hash_key       = "ipst"

  attribute {
    name = "ipst"
    type = "S"
  }

  tags = {
    Name        = "calcloud-model${local.environment}"
    Environment = "${local.environment}"
  }
}

module "lambda_model_ingest" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 1.43.0"

  function_name = "calcloud-model-ingest${local.environment}"

  #### NEW ROLE NEEDED HERE
  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_predict_role.value)
  ####

  description   = "looks for processed-ipppssoot.trigger messages, scrapes and uploads completed job data to DynamoDB"
  handler       = "lambda_scrape.lambda_handler"
  runtime       = "python3.8"
  publish       = false
  timeout       = 180
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  source_path = [
    {
      path = "${path.module}/../lambda/ModelIngest"
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

  environment_variables = {
    "DDBTABLE": "${aws_dynamodb_table.calcloud_model_db.name}"
  }

  tags = {
    Name = "calcloud-model-ingest${local.environment}"
  }
}

resource "aws_lambda_permission" "allow_bucket_ingestLambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_model_ingest.this_lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.calcloud.arn
  source_account = data.aws_caller_identity.this.account_id
}
