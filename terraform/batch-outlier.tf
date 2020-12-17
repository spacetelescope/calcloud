resource "aws_batch_job_queue" "batch_outlier_queue" {
  compute_environments = [
    aws_batch_compute_environment.calcloud_outlier.arn
  ]
  name = "calcloud-hst-outlier-queue"
  priority = 10
  state = "ENABLED"
  
}

resource "aws_batch_compute_environment" "calcloud_outlier" {
  compute_environment_name = "calcloud-hst-outlier"
  type = "MANAGED"
  service_role = var.aws_batch_job_role_arn

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
       "c5.9xlarge",      #  36 cores, 72G ram
    ]
    max_vcpus = 72
    min_vcpus = 0
    desired_vcpus = 0

    launch_template {
      launch_template_id = aws_launch_template.hstdp.id
    }
  }
  lifecycle { ignore_changes = [compute_resources.0.desired_vcpus] }
}

