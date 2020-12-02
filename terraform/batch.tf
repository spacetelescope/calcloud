# need a non-aliased provider to provide a default and stop terraform from prompting for a region
provider "aws" {
  region  = var.region
}

provider "aws" {
  profile = "HSTRepro_Sandbox"
  alias = "sandbox"
  region  = "us-east-1"
}

provider "aws" {
  profile = "HSTRepro_Dev"
  alias = "dev"
  region = "us-east-1"
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
  key_name                = var.keypair
  tags                    = {
    "Name"         = "calcloud-hst-worker"
    "calcloud-hst" = "calcloud-hst-worker"
  }
  user_data               = base64encode(data.template_file.userdata.rendered)
  vpc_security_group_ids  = [
        aws_security_group.batchsg.id,
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
    arn = aws_iam_instance_profile.ecs_instance_role.arn
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
  service_role = aws_iam_role.aws_batch_service_role.arn
  depends_on = [
    aws_iam_role_policy_attachment.aws_batch_service_role,
  ]

  compute_resources {
    allocation_strategy = "BEST_FIT"
    ec2_key_pair = var.keypair
    instance_role = aws_iam_instance_profile.ecs_instance_role.arn
    type = "EC2"
    bid_percentage = 0
    tags = {}
    subnets             = [aws_subnet.batch_sn.id]
    security_group_ids  = [
      aws_security_group.batchsg.id,
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
    "jobRoleArn": "${aws_iam_role.batch_job_role.arn}",
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

  depends_on = [
    aws_iam_role_policy_attachment.aws_batch_service_role
  ]
}

resource "aws_s3_bucket" "calcloud" {
  bucket = "calcloud-hst-pipeline-outputs-sandbox"
  provider = aws.sandbox
  tags = {
    "CALCLOUD" = "calcloud-hst-pipeline-outputs"
    "Name"     = "calcloud-hst-pipeline-outputs"
  }
}

resource "aws_s3_bucket_public_access_block" "s3_public_block" {
  provider = aws.sandbox
  bucket = aws_s3_bucket.calcloud.id

  block_public_acls   = true
  block_public_policy = true
  restrict_public_buckets = true
  ignore_public_acls = true
}


