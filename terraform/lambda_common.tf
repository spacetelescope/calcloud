# bucket to hold lambda envs
resource "aws_s3_bucket" "calcloud_lambda_envs" {
  bucket = "calcloud-lambda-envs${local.environment}"
  tags = {
    "Name"     = "calcloud-lambda-envs${local.environment}"
  }
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = "AES256"
      }
    }
  }
  force_destroy = true
}

# ssl requests policy
resource "aws_s3_bucket_policy" "ssl_only_lambda_envs" {
  bucket = aws_s3_bucket.calcloud_lambda_envs.id

  depends_on = [aws_s3_bucket_public_access_block.s3_lambda_public_block]

  # Terraform's "jsonencode" function converts a
  # Terraform expression's result to valid JSON syntax.
  policy = jsonencode({
    Id = "SSLPolicy",
    Version = "2012-10-17",
    Statement = [
        {
            Sid = "AllowSSLRequestsOnly",
            Action = "s3:*",
            Effect = "Deny",
            Principal = "*",
            Resource = [
                aws_s3_bucket.calcloud_lambda_envs.arn,
                "${aws_s3_bucket.calcloud_lambda_envs.arn}/*"
            ],
            Condition = {
                Bool = {
                     "aws:SecureTransport" = "false"
                }
            }
        }
    ]
  })
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

  lambda_function {
    lambda_function_arn = module.calcloud_lambda_deleteJob.this_lambda_function_arn
    events              = ["s3:ObjectCreated:Put"]
    filter_prefix       = "messages/cancel-"
  }
  
  lambda_function {
    lambda_function_arn = module.calcloud_lambda_rescueJob.this_lambda_function_arn
    events              = ["s3:ObjectCreated:Put"]
    filter_prefix       = "messages/rescue-"
  }

  lambda_function {
    lambda_function_arn = module.calcloud_lambda_broadcast.this_lambda_function_arn
    events              = ["s3:ObjectCreated:Put"]
    filter_prefix       = "messages/broadcast-"
  }

  depends_on = [
    aws_lambda_permission.allow_bucket,
    aws_lambda_permission.allow_bucket_deleteLambda,
    aws_lambda_permission.allow_bucket_rescueLambda,
    aws_lambda_permission.allow_bucket_broadcastLambda
  ]
}