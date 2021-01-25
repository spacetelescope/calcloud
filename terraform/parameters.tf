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

