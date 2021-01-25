provider "aws" {
  region  = var.region
}

data "template_file" "userdata" {
  template = file("${path.module}/user_data.sh")
  vars = {
      // Any var you need to pass to the script
  }
}

resource "aws_launch_template" "hstdp" {
  name = "calcloud-hst-worker${local.environment}"
  description             = "Template for cluster worker nodes updated to limit stopped container lifespan"
  ebs_optimized           = "false"
  image_id                = data.aws_ssm_parameter.batch_ami_id.value
  tags                    = {
    "Name"         = "calcloud-hst-worker${local.environment}"
    "calcloud-hst" = "calcloud-hst-worker${local.environment}"
  }
  user_data               = base64encode(data.template_file.userdata.rendered)

  vpc_security_group_ids  = local.batch_sgs

  block_device_mappings {
    device_name = "/dev/xvda"

  ebs {
    delete_on_termination = "true"
    encrypted             = "false"
    iops                  = 0
    volume_size           = 150
    volume_type           = "gp2"
            }
  }
  iam_instance_profile {
    arn = data.aws_ssm_parameter.ecs_instance_role.value
  }
  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      "Name" = "calcloud-hst-worker${local.environment}"
      "calcloud-hst" = "calcloud-hst-worker${local.environment}"
    }
  }

  tag_specifications {
    resource_type = "volume"
    tags = {
      "Name" = "calcloud-hst-worker${local.environment}"
      "calcloud-hst" = "calcloud-hst-worker${local.environment}"
    }
  }
}

resource "aws_batch_job_queue" "batch_queue" {
  name = "calcloud-hst-queue${local.environment}"
  compute_environments = [
    aws_batch_compute_environment.calcloud.arn
  ]
  priority = 10
  state = "ENABLED"

}

resource "aws_batch_compute_environment" "calcloud" {
  compute_environment_name  = "calcloud-hst${local.environment}"
  type = "MANAGED"
  service_role = data.aws_ssm_parameter.batch_service_role.value

  compute_resources {
    allocation_strategy = "BEST_FIT"
    instance_role = data.aws_ssm_parameter.ecs_instance_role.value
    type = "EC2"
    bid_percentage = 0
    tags = {}
    subnets             = local.batch_subnet_ids
    security_group_ids  = local.batch_sgs
    instance_type = [
      "m5.large",
      "m5.xlarge",
    ]
    max_vcpus = 128
    min_vcpus = 0
    desired_vcpus = 0

    launch_template {
      launch_template_id = aws_launch_template.hstdp.id
    }
  }
  lifecycle { ignore_changes = [compute_resources.0.desired_vcpus] }
}

resource "aws_ecr_repository" "caldp_ecr" {
  name                 = "caldp${local.environment}"
}

data "aws_ecr_image" "caldp_latest" {
  repository_name = aws_ecr_repository.caldp_ecr.name
  image_tag = var.image_tag
}

resource "aws_batch_job_definition" "calcloud" {
  name                 = "calcloud-hst-caldp-job-definition${local.environment}"
  type                 = "container"
  container_properties = <<CONTAINER_PROPERTIES
  {
    "command": ["Ref::command", "Ref::dataset", "Ref::input_path", "Ref::s3_output_path", "Ref::crds_config"],
    "environment": [],
    "image": "${aws_ecr_repository.caldp_ecr.repository_url}:${data.aws_ecr_image.caldp_latest.image_tag}",
    "jobRoleArn": data.aws_ssm_parameter.batch_job_role.value,
    "memory": 2560,
    "mountPoints": [],
    "resourceRequirements": [],
    "ulimits": [],
    "vcpus": 1,
    "volumes": []
  }
  CONTAINER_PROPERTIES

  parameters = {
    "command" = "caldp-process"
    "dataset" = "j8cb010b0"
    "input_path" = "astroquery:"
    "s3_output_path" = "s3://${aws_s3_bucket.calcloud.bucket}"
    "crds_config" = "caldp-config-offsite"
  }
}

resource "aws_s3_bucket" "calcloud" {
  bucket = "calcloud-hst-pipeline-outputs${local.environment}"
  tags = {
    "CALCLOUD" = "calcloud-hst-pipeline-outputs${local.environment}"
    "Name"     = "calcloud-hst-pipeline-outputs${local.environment}"
  }
}

resource "aws_s3_bucket_public_access_block" "s3_public_block" {
  bucket = aws_s3_bucket.calcloud.id

  block_public_acls   = true
  block_public_policy = true
  restrict_public_buckets = true
  ignore_public_acls=true
}
