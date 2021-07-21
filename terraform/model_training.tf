resource "aws_batch_job_queue" "model_queue" {
  name = "calcloud-model-training-queue${local.environment}"
  count = 1
  compute_environments = [aws_batch_compute_environment.model_compute_env[count.index].arn]
  priority = 10
  state = "ENABLED"
}

resource "aws_batch_compute_environment" "model_compute_env" {
  count = 1
  compute_environment_name_prefix = "calcloud-model-training${local.environment}"
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
    instance_type = ["c5a.2xlarge"]
    max_vcpus = 8
    min_vcpus = 0
    desired_vcpus = 0
  }
  lifecycle {
    ignore_changes = [compute_resources.0.desired_vcpus]
    create_before_destroy = true
  }
}

resource "aws_batch_job_definition" "model_job_def_main" {
  name                 = "calcloud-model-training-jobdef${local.environment}"
  count = 1
  type                 = "container"
  container_properties = <<CONTAINER_PROPERTIES
  {
    "command": ["python", "-m", "modeling.main"],
    "environment": [
      {"name": "S3MOD", "value": "calcloud-modeling${local.environment}"},
      {"name": "TIMESTAMP", "value": "now"},
      {"name": "VERBOSE", "value": "0"},
      {"name": "DATASOURCE", "value": "ddb"},
      {"name": "DDBTABLE", "value": "calcloud-model${local.environment}"},
      {"name": "KFOLD", "value": "None"},
      {"name": "ATTRNAME", "value": "None"},
      {"name": "ATTRMETHOD", "value": "None"},
      {"name": "ATTRVALUE", "value": "None"},
      {"name": "ATTRTYPE", "value": "None"},
      {"name": "NJOBS", "value": "-2"}
    ],
    "image": "${local.ecr_model_training_image}",
    "jobRoleArn": "${data.aws_ssm_parameter.batch_job_role.value}",
    "mountPoints": [],
    "resourceRequirements": [
        {"value" :  "2048", "type" : "MEMORY"},
        {"value" : "8", "type": "VCPU"}
    ],
    "ulimits": [],
    "volumes": []
  }
  CONTAINER_PROPERTIES
}
