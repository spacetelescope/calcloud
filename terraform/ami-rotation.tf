resource "aws_launch_template" "ami_rotation" {
  name = "calcloud-ami-rotation${local.environment}"
  description             = "launch template for running ami rotation via terraform"
  ebs_optimized           = "false"
  image_id                = nonsensitive(aws_ssm_parameter.ci_ami.value)
  update_default_version = true
  tags                    = {
    "Name"         = "calcloud-ami-rotation${local.environment}"
  }
  user_data               = base64encode(
      templatefile("${path.module}/../ami_rotation/ami_rotation_userdata.sh", {
          environment = var.environment,
          admin_arn = nonsensitive(data.aws_ssm_parameter.admin_arn.value),
          calcloud_ver = var.awsysver,
          log_group = aws_cloudwatch_log_group.ami-rotation.name
      })
  )

  vpc_security_group_ids  = local.batch_sgs
  instance_type = "t3.large"
  instance_initiated_shutdown_behavior = "terminate"

  block_device_mappings {
    device_name = "/dev/xvda"


  ebs {
    # see the aws batch launch template for some comments about valid ebs construction
    delete_on_termination = "true"
    encrypted             = "true"
    # must be >= 30 gb due to size of the base AMI created by IT
    volume_size           = 30
    volume_type           = "gp2"
            }
  }
  iam_instance_profile {
    arn = nonsensitive(data.aws_ssm_parameter.ci_instance_role.value)
  }
  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      "Name" = "calcloud-ami-rotation${local.environment}"
    }
  }

  tag_specifications {
    resource_type = "volume"
    tags = {
      "Name" = "calcloud-ami-rotation${local.environment}"
    }
  }
}

module "calcloud_env_amiRotation" {
  source = "terraform-aws-modules/lambda/aws"
  version = "~> 6.0.0"

  function_name = "calcloud-env-AmiRotation${local.environment}"
  description   = "spawns an ec2 bi-weekly which rotates the ami for batch"
  # the path is relative to the path inside the lambda env, not in the local filesystem.
  handler       = "ami_rotation.lambda_handler"
  runtime       = "python3.11"
  publish       = false
  timeout       = 60
  cloudwatch_logs_retention_in_days = local.lambda_log_retention_in_days

  source_path = [
    {
      # this is the lambda itself. The code in path will be placed directly into the lambda execution path
      path = "${path.module}/../lambda/AmiRotation"
      pip_requirements = false
    }
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

  lambda_role = nonsensitive(data.aws_ssm_parameter.lambda_amiRotate_role.value)

  environment_variables = merge(local.common_env_vars, {
    LAUNCH_TEMPLATE_NAME=aws_launch_template.ami_rotation.name,
    SUBNET = local.batch_subnet_ids[0]
  })

  tags = {
    Name = "calcloud-env-AmiRotation${local.environment}"
  }
}

resource "aws_cloudwatch_log_group" "ami-rotation" {
  name = "/tf/ec2/ami-rotation${local.environment}"
  retention_in_days = local.lambda_log_retention_in_days
}

resource "aws_cloudwatch_event_rule" "ami-rotate-scheduler" {
  name                = "ami-rotate-scheduler${local.environment}"
  description         = "scheduler for ami rotation"
  schedule_expression = "cron(0 8 ? * TUE,FRI *)"
  is_enabled = "false"   # disable because we now have CodeBuild project for AMI rotation
}

resource "aws_cloudwatch_event_target" "ami-rotate-scheduler" {
  rule      = aws_cloudwatch_event_rule.ami-rotate-scheduler.name
  target_id = "lambda"
  arn       = module.calcloud_env_amiRotation.lambda_function_arn
}

resource "aws_lambda_permission" "allow_lambda_exec_ami_rotate" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = module.calcloud_env_amiRotation.lambda_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ami-rotate-scheduler.arn
}
