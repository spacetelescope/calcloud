provider "aws" {
  region  = var.region
}

terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 3.29.0"
    }
    hashicorp-template = {
      source = "hashicorp/template"
      version = "~> 2.2.0"
    }
    hashicorp-null = {
      source = "hashicorp/null"
      version = "~> 3.1.0"
    }
    hashicorp-external = {
      source = "hashicorp/external"
      version = "~> 2.1.0"
    }
    hashicorp-local = {
      source = "hashicorp/local"
      version = "~> 2.1.0"
    }
    hashicorp-random = {
      source = "hashicorp/random"
      version = "~> 3.1.0"
    }
  }
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
  update_default_version = true
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
    encrypted             = "true"
    # iops is only valid for gp3, io1, io2 (not gp2)
    iops                  = lookup(var.lt_ebs_iops, local.environment, 0)
    # throughput is only valid for gp3
    throughput            = lookup(var.lt_ebs_throughput, local.environment, 0)
    volume_size           = 150
    volume_type           = lookup(var.lt_ebs_type, local.environment, "gp2")
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
  compute_environment_name_prefix = "calcloud-hst${local.environment}-"
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
    instance_type = ["optimal"]
    max_vcpus = 128
    min_vcpus = 0
    desired_vcpus = 0

    launch_template {
      launch_template_id = aws_launch_template.hstdp.id
      version = "$Latest"
    }
  }
  lifecycle { 
    ignore_changes = [compute_resources.0.desired_vcpus]
    create_before_destroy = true 
  }
}

resource "aws_ecr_repository" "caldp_ecr" {
  name                 = "caldp${local.environment}"
  image_scanning_configuration {
    scan_on_push = true
  }
}

data "aws_ecr_image" "caldp_latest" {
  repository_name = aws_ecr_repository.caldp_ecr.name
  image_tag = var.image_tag
}

# ------------------------------------------------------------------------------------------

# 2G -----------------  also reserve 128M per 1G for Batch ECS + STScI overheads

resource "aws_batch_job_definition" "calcloud_2g" {
  name                 = "calcloud-jobdef-2g${local.environment}"
  type                 = "container"
  container_properties = <<CONTAINER_PROPERTIES
  {
    "command": ["Ref::command", "Ref::dataset", "Ref::input_path", "Ref::s3_output_path", "Ref::crds_config"],
    "environment": [
      {"name": "AWSDPVER", "value": "${var.awsdpver}"},
      {"name": "AWSYSVER", "value": "${var.awsysver}"},
      {"name": "CSYS_VER", "value": "${var.csys_ver}"}
    ],
    "image": "${aws_ecr_repository.caldp_ecr.repository_url}:${data.aws_ecr_image.caldp_latest.image_tag}",
    "jobRoleArn": "${data.aws_ssm_parameter.batch_job_role.value}",
    "mountPoints": [],
    "resourceRequirements": [
        {"value" : "${2*(1024-128)}", "type" : "MEMORY"},
        {"value" : "1", "type": "VCPU"}
    ],
    "ulimits": [],
    "volumes": []
  }
  CONTAINER_PROPERTIES

  parameters = {
    "command" = "caldp-process"
    "dataset" = "j8cb010b0"
    "input_path" = "astroquery:"
    "s3_output_path" = "s3://${aws_s3_bucket.calcloud.bucket}/outputs"
    "crds_config" = "caldp-config-offsite"
  }
}

# 8G ----------------

resource "aws_batch_job_definition" "calcloud_8g" {
  name                 = "calcloud-jobdef-8g${local.environment}"
  type                 = "container"
  container_properties = <<CONTAINER_PROPERTIES
  {
    "command": ["Ref::command", "Ref::dataset", "Ref::input_path", "Ref::s3_output_path", "Ref::crds_config"],
    "environment": [
      {"name": "AWSDPVER", "value": "${var.awsdpver}"},
      {"name": "AWSYSVER", "value": "${var.awsysver}"},
      {"name": "CSYS_VER", "value": "${var.csys_ver}"}
    ],
    "image": "${aws_ecr_repository.caldp_ecr.repository_url}:${data.aws_ecr_image.caldp_latest.image_tag}",
    "jobRoleArn": "${data.aws_ssm_parameter.batch_job_role.value}",
    "mountPoints": [],
    "resourceRequirements": [
        {"value" : "${8*(1024-128)}", "type" : "MEMORY"},
        {"value" : "4", "type": "VCPU"}
    ],
    "ulimits": [],
    "volumes": []
  }
  CONTAINER_PROPERTIES

  parameters = {
    "command" = "caldp-process"
    "dataset" = "j8cb010b0"
    "input_path" = "astroquery:"
    "s3_output_path" = "s3://${aws_s3_bucket.calcloud.bucket}/outputs"
    "crds_config" = "caldp-config-offsite"
  }
}

# 16G -------------------

resource "aws_batch_job_definition" "calcloud_16g" {
  name                 = "calcloud-jobdef-16g${local.environment}"
  type                 = "container"
  container_properties = <<CONTAINER_PROPERTIES
  {
    "command": ["Ref::command", "Ref::dataset", "Ref::input_path", "Ref::s3_output_path", "Ref::crds_config"],
    "environment": [
      {"name": "AWSDPVER", "value": "${var.awsdpver}"},
      {"name": "AWSYSVER", "value": "${var.awsysver}"},
      {"name": "CSYS_VER", "value": "${var.csys_ver}"}
    ],
    "image": "${aws_ecr_repository.caldp_ecr.repository_url}:${data.aws_ecr_image.caldp_latest.image_tag}",
    "jobRoleArn": "${data.aws_ssm_parameter.batch_job_role.value}",
    "mountPoints": [],
    "resourceRequirements": [
        {"value": "${16*(1024-128)}", "type": "MEMORY"},
        {"value": "8", "type": "VCPU"}
    ],
    "ulimits": [],
    "volumes": []
  }
  CONTAINER_PROPERTIES

  parameters = {
    "command" = "caldp-process"
    "dataset" = "j8cb010b0"
    "input_path" = "astroquery:"
    "s3_output_path" = "s3://${aws_s3_bucket.calcloud.bucket}/outputs"
    "crds_config" = "caldp-config-offsite"
  }
}

# 64G ------------------

resource "aws_batch_job_definition" "calcloud_64g" {
  name                 = "calcloud-jobdef-64g${local.environment}"
  type                 = "container"
  container_properties = <<CONTAINER_PROPERTIES
  {
    "command": ["Ref::command", "Ref::dataset", "Ref::input_path", "Ref::s3_output_path", "Ref::crds_config"],
    "environment": [
      {"name": "AWSDPVER", "value": "${var.awsdpver}"},
      {"name": "AWSYSVER", "value": "${var.awsysver}"},
      {"name": "CSYS_VER", "value": "${var.csys_ver}"}
    ],
    "image": "${aws_ecr_repository.caldp_ecr.repository_url}:${data.aws_ecr_image.caldp_latest.image_tag}",
    "jobRoleArn": "${data.aws_ssm_parameter.batch_job_role.value}",
    "mountPoints": [],
    "resourceRequirements": [
        {"value": "${64*(1024-128)}", "type": "MEMORY"},
        {"value": "32", "type": "VCPU"}
    ],
    "ulimits": [],
    "volumes": []
  }
  CONTAINER_PROPERTIES

  parameters = {
    "command" = "caldp-process"
    "dataset" = "j8cb010b0"
    "input_path" = "astroquery:"
    "s3_output_path" = "s3://${aws_s3_bucket.calcloud.bucket}/outputs"
    "crds_config" = "caldp-config-offsite"
  }
}

# ---------------------------------------------------------------------------------------------

resource "aws_s3_bucket" "calcloud" {
  bucket = "calcloud-processing${local.environment}"
  force_destroy = true
  tags = {
    "CALCLOUD" = "calcloud-processing${local.environment}"
    "Name"     = "calcloud-processing${local.environment}"
  }
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm     = "AES256"
      }
    }
  }
}

resource "aws_s3_bucket_public_access_block" "s3_public_block" {
  bucket = aws_s3_bucket.calcloud.id

  block_public_acls   = true
  block_public_policy = true
  restrict_public_buckets = true
  ignore_public_acls=true
}

# ssl requests policy
resource "aws_s3_bucket_policy" "ssl_only_processing" {
  bucket = aws_s3_bucket.calcloud.id

  depends_on = [aws_s3_bucket_public_access_block.s3_public_block]

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
                aws_s3_bucket.calcloud.arn,
                "${aws_s3_bucket.calcloud.arn}/*"
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
