data aws_ssm_parameter batch_ami_id {
  name = "/AMI/STSCI-HST-REPRO-ECS"
}

data aws_ssm_parameter batch_subnet_ids {
  name = "/subnets/private"
}

data aws_ssm_parameter batch_job_role {
  name = "/iam/roles/aws_batch_job_role"
}

data aws_ssm_parameter batch_service_role {
  name = "/iam/roles/aws_batch_service_role"
}

data aws_ssm_parameter ecs_instance_role {
  name = "/iam/roles/ecs_instance_role"
}

data aws_ssm_parameter batch_sgs {
  name = "/vpc/sgs/batch"
}

data aws_ssm_parameter environment {
  name = "environment"
}

data aws_ssm_parameter vpc {
   name = "vpc"
}

data aws_ssm_parameter lambda_submit_role {
  name = "/iam/roles/calcloud_lambda_submit"
}

data aws_ssm_parameter lambda_blackboard_role {
  name = "/iam/roles/calcloud_lambda_blackboard"
}

data aws_ssm_parameter lambda_delete_role {
  name = "/iam/roles/calcloud_lambda_delete"
}

data aws_ssm_parameter lambda_cleanup_role {
  name = "/iam/roles/calcloud_lambda_cleanup"
}

data aws_ssm_parameter lambda_broadcast_role {
  name = "/iam/roles/calcloud_lambda_broadcast"
}

data aws_ssm_parameter lambda_cloudwatch_role {
  name = "/iam/roles/calcloud_lambda_cloudWatchLogs"
}

data aws_ssm_parameter lambda_refreshCacheSubmit_role {
  name = "/iam/roles/calcloud_lambda_refreshCacheSubmit"
}

data aws_ssm_parameter file_share_arn {
  name = "/gateway/fileshare"
}
