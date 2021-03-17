

resource "aws_ecr_repository" "calcloud_predict_ecr" {
  name                 = "calcloud-predict${local.environment}"
  image_scanning_configuration {
    scan_on_push = true
  }
}

data "aws_ecr_image" "calcloud_predict_latest" {
  repository_name = aws_ecr_repository.calcloud_predict_ecr.name
  image_tag = var.image_tag
}

module "lambda_function_container_image" {
  source = "terraform-aws-modules/lambda/aws"

  function_name = "calcloud-predict${local.environment}"
  description   = "pretrained neural networks to generate predictions on job resource requirements (memory bin and max execution time)"

  create_package = false
  image_uri = aws_ecr_image.calcloud_predict_latest.repository_name
  #image_uri    = "218835028644.dkr.ecr.us-east-1.amazonaws.com/calcloud-ai"
  package_type = "Image"

  timeout       = 180
  memory        = 500
  cloudwatch_logs_retention_in_days = 30

  source_path = [
    {
      # this is the lambda itself. The code in path will be placed directly into the lambda execution path
      path = "${path.module}/../lambda/JobPredict"
      pip_requirements = false
    }
  ]

  #store_on_s3 = true
  #s3_bucket   = aws_s3_bucket.calcloud_lambda_envs.id

  # ensures that terraform doesn't try to mess with IAM
  create_role = false
  attach_cloudwatch_logs_policy = false
  attach_dead_letter_policy = false
  attach_network_policy = false
  attach_tracing_policy = false
  attach_async_event_policy = false
  # existing role for the lambda
  # will need to parametrize when ITSD takes over role creation.
  # for now this role was created by hand in the console, it is not terraform managed
  lambda_role = data.aws_ssm_parameter.lambda_predict_role.value

  tags = {
    Name = "calcloud-job-predict${local.environment}"
  }
}

# for invoking container image lambda (memory prediction model)
resource "aws_lambda_permission" "invoke_function" {
  # statement_id  = "lambda-401751db-99b5-4e48-a26b-ed07bd237bfd"
  statement_id  = "AllowInvocationFromSubmitJobLambda"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_function_container_image.this_lambda_function_arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.calcloud.arn
}
