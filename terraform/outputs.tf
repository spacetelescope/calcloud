output batch_ami_id {
  value       = data.aws_ssm_parameter.batch_ami_id.value
  description = "AMI ID ssm parameter, for ITSD's latest Batch worker AMI"
}

output batch_subnet_ids {
  value       = local.batch_subnet_ids
  description = "ID ssm parameter for subnets used by AWS batch"
}

output batch_job_role {
  value = data.aws_ssm_parameter.batch_job_role.value
}

output batch_service_role {
  value = data.aws_ssm_parameter.batch_service_role.value
}

output ecs_instance_role {
  value = data.aws_ssm_parameter.ecs_instance_role.value
}

output batch_sgs {
  value = local.batch_sgs
}

output environment {
  value = local.environment
}

output region {
  value = var.region
}

output vpc {
  value = data.aws_ssm_parameter.vpc.value
}

output predict_lambda_function_arn {
  value = module.lambda_function_container_image.this_lambda_function_arn
}

output s3_output_bucket {
  value = aws_s3_bucket.calcloud.id
}

output crds_context {
  value = lookup(var.crds_context, local.environment, var.crds_context["-sb"])
}