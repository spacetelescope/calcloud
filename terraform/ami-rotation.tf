data "template_file" "ami_rotation_userdata" {
  template = file("${path.module}/../ami_rotation/ami_rotation_userdata.sh")
  vars = {
      environment = var.environment,
      admin_arn = nonsensitive(data.aws_ssm_parameter.admin_arn.value),
      calcloud_ver = var.awsysver,
      log_group = aws_cloudwatch_log_group.ami-rotation.name
  }
}

resource "aws_launch_template" "ami_rotation" {
  name = "calcloud-ami-rotation${local.environment}"
  description             = "launch template for running ami rotation via terraform"
  ebs_optimized           = "false"
  image_id                = nonsensitive(aws_ssm_parameter.repro_ami.value)
  update_default_version = true
  tags                    = {
    "Name"         = "calcloud-ami-rotation${local.environment}"
  }
  user_data               = base64encode(data.template_file.ami_rotation_userdata.rendered)

  vpc_security_group_ids  = local.batch_sgs
  instance_type = "t3.large"
  instance_initiated_shutdown_behavior = "terminate"

  block_device_mappings {
    device_name = "/dev/xvda"


  ebs {
    # IF YOU CHANGE THE LAUNCH TEMPLATE YOU MUST "TAINT" THE COMPUTE ENVIRONMENT BEFORE DEPLOY
    # IN ORDER FOR YOUR CHANGES TO BE PICKED UP BY BATCH
    # SAYING IT AGAIN IN THE PLACE WHERE YOU MAY BE TRYING TO MAKE A CHANGE TO THE TEMPLATE
    delete_on_termination = "true"
    encrypted             = "true"
    # iops is only valid for gp3, io1, io2 (not gp2)
    # iops                  = lookup(var.lt_ebs_iops, local.environment, 0)
    # throughput is only valid for gp3, but it doesn't accept '0' as valid. null works, which is then set to 0
    # throughput            = lookup(var.lt_ebs_throughput, local.environment, null)
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
  version = "~> 1.43.0"

  function_name = "calcloud-env-AmiRotation${local.environment}"
  description   = "spawns an ec2 weekly which rotates the ami for batch"
  # the path is relative to the path inside the lambda env, not in the local filesystem.
  handler       = "ami_rotation.lambda_handler"
  runtime       = "python3.6"
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

  lambda_role = "arn:aws:iam::218835028644:role/calcloud-lambda-AmiRotation"

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