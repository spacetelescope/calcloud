resource "aws_batch_job_queue" "batch_outlier_queue" {
  name = "calcloud-hst-outlier-queue${local.environment}"
  compute_environments = [
    aws_batch_compute_environment.calcloud_outlier.arn
  ]
  priority = 10
  state = "ENABLED"

}

resource "aws_batch_compute_environment" "calcloud_outlier" {
  compute_environment_name = "calcloud-hst-outlier${local.environment}"
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
