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

data aws_ssm_parameter lambda_predict_role {
  name = "/iam/roles/calcloud_lambda_predict"
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

data aws_ssm_parameter fs_blackboard_arn {
  name = "/gateway/fileshare/blackboard"
}

data aws_ssm_parameter fs_control_arn {
  name = "/gateway/fileshare/control"
}

data aws_ssm_parameter fs_crds_arn {
  name = "/gateway/fileshare/crds_env_vars"
}

data aws_ssm_parameter fs_inputs_arn {
  name = "/gateway/fileshare/inputs"
}

data aws_ssm_parameter fs_messages_arn {
  name = "/gateway/fileshare/messages"
}

data aws_ssm_parameter fs_outputs_arn {
  name = "/gateway/fileshare/outputs"
}

data aws_ssm_parameter lambda_rescue_role {
  name = "/iam/roles/calcloud_lambda_rescue"
}

data aws_ssm_parameter crds_ops {
  name = "/s3/external/crds-ops"
}

data aws_ssm_parameter crds_test {
  name = "/s3/external/crds-test"
}
