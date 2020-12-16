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

