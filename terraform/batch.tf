

provider "aws" {
  region  = var.region
}

terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 5.17.0"
    }
    hashicorp-null = {
      source = "hashicorp/null"
      version = "~> 3.2.1"
    }
    hashicorp-external = {
      source = "hashicorp/external"
      version = "~> 2.3.1"
    }
    hashicorp-local = {
      source = "hashicorp/local"
      version = "~> 2.4.0"
    }
    hashicorp-random = {
      source = "hashicorp/random"
      version = "~> 3.5.1"
    }
    docker = {
      source = "kreuzwerker/docker"
      version = "~> 3.0.2"
    }
  }
}

# See also lambda module version in each lambda .tf file

resource "aws_launch_template" "hstdp" {
  # IF YOU CHANGE THE LAUNCH TEMPLATE YOU MUST "TAINT" THE COMPUTE ENVIRONMENT BEFORE DEPLOY
  # IN ORDER FOR YOUR CHANGES TO BE PICKED UP BY BATCH
  # See https://docs.aws.amazon.com/batch/latest/userguide/create-compute-environment.html
  # and https://github.com/hashicorp/terraform-provider-aws/issues/15535
  name = "calcloud-hst-worker${local.environment}"
  description             = "Template for cluster worker nodes updated to limit stopped container lifespan"
  ebs_optimized           = "false"
  image_id                = nonsensitive(aws_ssm_parameter.ecs_ami.value)
  update_default_version = true
  tags                    = {
    "Name"         = "calcloud-hst-worker${local.environment}"
    "calcloud-hst" = "calcloud-hst-worker${local.environment}"
  }
  user_data               = base64encode(templatefile("${path.module}/user_data.sh", {}))

  vpc_security_group_ids  = local.batch_sgs

  block_device_mappings {
    device_name = "/dev/xvda"

  ebs {
    # IF YOU CHANGE THE LAUNCH TEMPLATE YOU MUST "TAINT" THE COMPUTE ENVIRONMENT BEFORE DEPLOY
    # IN ORDER FOR YOUR CHANGES TO BE PICKED UP BY BATCH
    # SAYING IT AGAIN IN THE PLACE WHERE YOU MAY BE TRYING TO MAKE A CHANGE TO THE TEMPLATE
    delete_on_termination = "true"
    encrypted             = "true"
    # iops is only valid for gp3, io1, io2 (not gp2)
    iops                  = lookup(var.lt_ebs_iops, local.environment, 0)
    # throughput is only valid for gp3, but it doesn't accept '0' as valid. null works, which is then set to 0
    throughput            = lookup(var.lt_ebs_throughput, local.environment, null)
    volume_size           = 150
    volume_type           = lookup(var.lt_ebs_type, local.environment, "gp2")
            }
  }
  iam_instance_profile {
    arn = nonsensitive(data.aws_ssm_parameter.ecs_instance_role.value)
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
  name = "calcloud-hst-queue-${local.ladder[count.index].name}${local.environment}"
  count = 4
  compute_environments = [aws_batch_compute_environment.compute_env[count.index].arn]
  priority = 10   # need to vectorize?
  state = "ENABLED"
}

resource "aws_batch_compute_environment" "compute_env" {
  count = 4
  compute_environment_name_prefix = "calcloud-hst-${local.ladder[count.index].name}${local.environment}"
  type = "MANAGED"
  service_role = nonsensitive(data.aws_ssm_parameter.batch_service_role.value)

  compute_resources {
    allocation_strategy = "BEST_FIT"
    instance_role = nonsensitive(data.aws_ssm_parameter.ecs_instance_role.value)
    type = "EC2"
    bid_percentage = 0
    tags = {}
    subnets             = local.batch_subnet_ids
    security_group_ids  = local.batch_sgs
    instance_type = local.ladder[count.index].ce_instance_type
    max_vcpus = local.ladder[count.index].ce_max_vcpus
    min_vcpus = local.ladder[count.index].ce_min_vcpus
    desired_vcpus = local.ladder[count.index].ce_desired_vcpus

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

# ------------------------------------------------------------------------------------------

# Env setting to simulate caught errors:
#      {"name": "CALDP_SIMULATE_ERROR", "value": "32"}

resource "aws_batch_job_definition" "job_def" {
  name                 = "calcloud-jobdef-${local.ladder[count.index].name}${local.environment}"
  count = 4
  type                 = "container"
  container_properties = <<CONTAINER_PROPERTIES
  {
    "command": ["Ref::command", "Ref::dataset", "Ref::input_path", "Ref::s3_output_path", "Ref::crds_config"],
    "environment": [
      {"name": "AWSDPVER", "value": "${var.awsdpver}"},
      {"name": "AWSYSVER", "value": "${var.awsysver}"},
      {"name": "CSYS_VER", "value": "${var.csys_ver}"},
      {"name": "CRDSBUCKET", "value": "${local.crds_bucket}"}
    ],
    "image": "${local.ecr_caldp_batch_image}",
    "jobRoleArn": "${nonsensitive(data.aws_ssm_parameter.batch_job_role.value)}",
    "executionRoleArn": "${nonsensitive(data.aws_ssm_parameter.batch_exec.value)}",
    "user": "developer",
    "privileged": false,
    "mountPoints": [],
    "resourceRequirements": [
        {"value" :  "${local.ladder[count.index].jd_memory}", "type" : "MEMORY"},
        {"value" : "${local.ladder[count.index].jd_vcpu}", "type": "VCPU"}
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

resource "aws_cloudwatch_query_definition" "batch_logstream_by_ipst" {
  name = "Batch-Logs-by-ipst${local.environment}"

  log_group_names = [
    "/aws/batch/job"
  ]

  query_string = <<EOF
fields @message, @logStream
| filter @message like /ipppssoot/
| head 1
EOF
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
