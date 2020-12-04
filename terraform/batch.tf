provider "aws" {
  region  = var.region
}

data "template_file" "userdata" {
  template = "${file("${path.module}/user_data.sh")}"
  vars = {
      // Any var you need to pass to the script
  }
}

resource "aws_launch_template" "hstdp" {
  description             = "Template for cluster worker nodes updated to limit stopped container lifespan"
  ebs_optimized           = "false"
  image_id                = "ami-07a63940735aebd38" # this is an amazon ECS community AMI
  tags                    = {
    "Name"         = "calcloud-hst-worker"
    "calcloud-hst" = "calcloud-hst-worker"
  }
  user_data               = base64encode(data.template_file.userdata.rendered)
  vpc_security_group_ids  = [
        var.batchsg_id,
  ]
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
    arn = var.ecs_instance_role_arn
  }
  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      "Name" = "calcloud-hst-worker"
      "calcloud-hst" = "calcloud-hst-worker"
    }
  }

  tag_specifications {
    resource_type = "volume"
    tags = {
      "Name" = "calcloud-hst-worker"
      "calcloud-hst" = "calcloud-hst-worker"
    }
  }
}

resource "aws_batch_job_queue" "batch_queue" {
  compute_environments = [
    aws_batch_compute_environment.calcloud.arn
  ]
  name = "calcloud-hst-queue"
  priority = 10
  state = "ENABLED"
  
}

resource "aws_batch_compute_environment" "calcloud" {
  type = "MANAGED"
  service_role = var.aws_batch_service_role_arn

  compute_resources {
    allocation_strategy = "BEST_FIT"
    instance_role = var.ecs_instance_role_arn
    type = "EC2"
    bid_percentage = 0
    tags = {}
    subnets             = [var.single_batch_subnet_id]
    security_group_ids  = [
      var.batchsg_id,
    ]
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
  name                 = "caldp"
}

data "aws_ecr_image" "caldp_latest" {
  repository_name = "${aws_ecr_repository.caldp_ecr.name}"
  image_tag = var.image_tag
}

resource "aws_batch_job_definition" "calcloud" {
  name                 = "calcloud-hst-caldp-job-definition"
  type                 = "container"
  container_properties = <<CONTAINER_PROPERTIES
  { 
    "command": ["Ref::command", "Ref::dataset", "Ref::input_path", "Ref::s3_output_path", "Ref::crds_config"],
    "environment": [],
    "image": "${aws_ecr_repository.caldp_ecr.repository_url}:${data.aws_ecr_image.caldp_latest.image_tag}",
    "jobRoleArn": "${var.aws_batch_job_role_arn}",
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
  bucket = "calcloud-hst-pipeline-outputs-sandbox"
  tags = {
    "CALCLOUD" = "calcloud-hst-pipeline-outputs"
    "Name"     = "calcloud-hst-pipeline-outputs"
  }
}

resource "aws_s3_bucket_public_access_block" "s3_public_block" {
  bucket = aws_s3_bucket.calcloud.id

  block_public_acls   = true
  block_public_policy = true
  restrict_public_buckets = true
  ignore_public_acls=true
}