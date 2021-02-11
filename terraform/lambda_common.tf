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