resource "aws_launch_template" "ami_rotation" {
  name = "calcloud-ami-rotation${local.environment}"
  description             = "launch template for running ami rotation via terraform"
  ebs_optimized           = false
  image_id                = nonsensitive(aws_ssm_parameter.ci_ami.value)
  update_default_version = true
  tags = {
    "Name"            = "calcloud-ami-rotation${local.environment}"
    "stsci-poc-email" = var.stsci_poc_email
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
      "Name"            = "calcloud-ami-rotation${local.environment}"
      "stsci-poc-email" = var.stsci_poc_email
    }
  }

  tag_specifications {
    resource_type = "volume"
    tags = {
      "Name"            = "calcloud-ami-rotation${local.environment}"
      "stsci-poc-email" = var.stsci_poc_email
    }
  }
}

resource "aws_cloudwatch_log_group" "ami-rotation" {
  name              = "/tf/ec2/ami-rotation${local.environment}"
  retention_in_days = local.lambda_log_retention_in_days
  tags = {
    "stsci-poc-email" = var.stsci_poc_email
  }
}

