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

data aws_ssm_parameter codebuild_role_name {
  name = "/hst-repro/codebuild-role"
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

data aws_ssm_parameter admin_arn {
  name = "/iam/roles/calcloud_admin"
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

data aws_ssm_parameter lambda_amiRotate_role {
  name = "/iam/roles/calcloud_lambda_amiRotate"
}

data aws_ssm_parameter model_ingest_role {
  name = "/iam/roles/calcloud_model_ingest"
}

#data aws_ssm_parameter codebuild_ami_rotate_svc_arn {
#  name = "/iam/roles/calcloud_codebuild_ami_rotate_svc_arn"
#}

#data aws_ssm_parameter codebuild_ami_rotate_deploy_arn {
#  name = "/iam/roles/calcloud_codebuild_ami_rotate_deploy_arn"
#}

#data aws_ssm_parameter aws_eventbridge_invoke_codebuild {
#  name = "/iam/roles/aws_eventbridge_invoke_codebuild"
#}

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

data aws_ssm_parameter model_bucket {
  name = "/s3/modeling"
}

data aws_ssm_parameter batch_exec {
  name = "/iam/roles/batch_exec"
}

data aws_ssm_parameter ci_instance_role {
  name = "/iam/roles/ci_instance_role"
}

data aws_ssm_parameter central_ecr {
  name = "/ecr/SharedServices"
}

resource "aws_ssm_parameter" "ami_rotation_base_image" {
  name  = "/tf/env/calcloud-ami-rotation-base-image${local.environment}"
  type  = "String"
  value = "${var.ami_rotation_base_image}"
  overwrite = true 
}


resource "aws_ssm_parameter" "awsysver" {
  name  = "/tf/env/awsysver${local.environment}"
  type  = "String"
  value = "${var.awsysver}"
  overwrite = true
}

resource "aws_ssm_parameter" "awsdpver" {
  name  = "/tf/env/awsdpver${local.environment}"
  type  = "String"
  value = "${var.awsdpver}"
  overwrite = true
}

resource "aws_ssm_parameter" "csys_ver" {
  name  = "/tf/env/csys_ver${local.environment}"
  type  = "String"
  value = "${var.csys_ver}"
  overwrite = true
}

resource "aws_ssm_parameter" "ecs_ami" {
  name = "/tf/ami/stsci-hst-repro-ecs${local.environment}"
  type = "String"
  value = "${var.ecs_ami}"
  overwrite = true
}

resource "aws_ssm_parameter" "ci_ami" {
  name = "/tf/ami/stsci-hst-amazon-linux-2${local.environment}"
  type = "String"
  value = "${var.ci_ami}"
  overwrite = true
}
