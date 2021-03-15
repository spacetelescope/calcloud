module "lambda_function_container_image" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "calcloud-ai${local.environment}"
  description   = "pretrained neural networks to generate predictions on job resource requirements (memory bin and max execution time)"

  create_package = false

  image_uri    = "218835028644.dkr.ecr.us-east-1.amazonaws.com/calcloud-ai"
  package_type = "Image"
}

# for invoking container image lambda (memory prediction model)
resource "aws_lambda_permission" "invoke_function" {
  statement_id  = "lambda-401751db-99b5-4e48-a26b-ed07bd237bfd"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_function_container_image.this_lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.calcloud.arn
}