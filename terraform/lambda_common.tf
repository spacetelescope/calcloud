# bucket to hold lambda envs
resource "aws_s3_bucket" "calcloud_lambda_envs" {
  bucket = "calcloud-lambda-envs${local.environment}"
  tags = {
    "Name"     = "calcloud-lambda-envs${local.environment}"
  }
  force_destroy = true
}

# locks down the lambda env bucket
resource "aws_s3_bucket_public_access_block" "s3_lambda_public_block" {
  bucket = aws_s3_bucket.calcloud_lambda_envs.id

  block_public_acls   = true
  block_public_policy = true
  restrict_public_buckets = true
  ignore_public_acls=true
}

# for s3 event trigger
# this is in common because multiple lambdas need to be defined in a single
# aws_s3_bucket_notification objects; multiples can't exist together.
# see terraform docs for aws_s3_bucket_notification
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.calcloud.id

  lambda_function {
    lambda_function_arn = module.calcloud_lambda_submit.this_lambda_function_arn
    events              = ["s3:ObjectCreated:Put"]
    filter_prefix       = "messages/placed-"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}