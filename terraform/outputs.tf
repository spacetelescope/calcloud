output ecs_ami_id {
  value       = nonsensitive(aws_ssm_parameter.ecs_ami.value)
  description = "AMI ID ssm parameter, for ITSD's latest Batch worker AMI"
}

output batch_subnet_ids {
  value       = local.batch_subnet_ids
  description = "ID ssm parameter for subnets used by AWS batch"
}

output batch_job_role {
  value = nonsensitive(data.aws_ssm_parameter.batch_job_role.value)
}

output batch_service_role {
  value = nonsensitive(data.aws_ssm_parameter.batch_service_role.value)
}

output ecs_instance_role {
  value = nonsensitive(data.aws_ssm_parameter.ecs_instance_role.value)
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
  value = nonsensitive(data.aws_ssm_parameter.vpc.value)
}

output predict_lambda_function_arn {
  value = module.lambda_function_container_image.lambda_function_arn
}

output s3_output_bucket {
  value = aws_s3_bucket.calcloud.id
}

output crds_context {
  value = lookup(var.crds_context, local.environment, var.crds_context["-sb"])
}

output common_env_vars {
  value = local.common_env_vars
}

output common_image_tag {
  value = local.common_image_tag
}

output ecr_predict_lambda_image {
  value = local.ecr_predict_lambda_image
}

output ecr_model_training_image {
  value = local.ecr_model_training_image
}

output ecr_caldp_batch_image {
  value = local.ecr_caldp_batch_image
}
