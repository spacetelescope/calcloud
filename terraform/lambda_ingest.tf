resource "aws_dynamodb_table" "calcloud_hst_db" {
  name           = "calcloud-hst-db"
  billing_mode   = "PROVISIONED"
  read_capacity  = 10
  write_capacity = 10
  hash_key       = "ipst"

  attribute {
    name = "ipst"
    type = "S"
  }

  tags = {
    Name        = "calcloud-hst-db"
    Environment = "${local.environment}"
  }
}

module "calcloud_lambda_ingest" {
  source = "terraform-aws-modules/lambda/aws"
  function_name = "calcloud-ingest${local.environment}"
  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_predict_role.value)
  description   = "looks for processed-ipppssoot.trigger messages, scrapes and uploads completed job data to DynamoDB"
  handler       = "lambda_scrape.lambda_handler"
  runtime       = "python3.8"
  create_package       = false
  timeout       = 180
  s3_existing_package = {
    bucket = "calcloud-modeling${local.environment}"
    key = "lambda/calcloud-ingest.zip"
  }
  publish = true
  store_on_s3 = true
  s3_bucket   = aws_s3_bucket.calcloud_lambda_envs.id
  create_role = false
  attach_cloudwatch_logs_policy = false
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  environment_variables = {
    "DDBTABLE": "${aws_dynamodb_table.calcloud_hst_db.name}"
  }

  tags = {
    Name = "calcloud-lambda-ingest${local.environment}"
  }
}

resource "aws_lambda_permission" "allow_bucket_ingestLambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_lambda_ingest.this_lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.calcloud.arn
  source_account = data.aws_caller_identity.this.account_id
}
