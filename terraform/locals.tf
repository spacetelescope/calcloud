data "aws_caller_identity" "this" {}
data "aws_region" "current" {}
data "aws_ecr_authorization_token" "token" {}

locals {
       batch_subnet_ids = split(",", nonsensitive(data.aws_ssm_parameter.batch_subnet_ids.value))

       batch_sgs = split(",", nonsensitive(data.aws_ssm_parameter.batch_sgs.value))

       # SSM environment value can be overridden,  also tweaked with "-" below
       pre_environment = var.environment != null ? var.environment : nonsensitive(data.aws_ssm_parameter.environment.value)

       # Unless the pre_environment is an empty string,  prepend an implicit "-" to the final environment value
       environment = local.pre_environment == "" ? "" : join("", ["-", local.pre_environment])

       job_definitions = join(",", aws_batch_job_definition.job_def[*].name)   # for env vars

       job_queues = join(",", aws_batch_job_queue.batch_queue[*].name)   # for env vars

       # Reserving 128M/1024M for ECS overheads
       ladder = [
              { # -------------------------------------------------------------------
                name : "02g",

                # 2g job def -> 2g queue -> 2g compute env
                ce_instance_type = [
                    "c5a.2xlarge",    #  8 cores,  16G    $0.308 / hr, 8 concurrent jobs
                 ],
                ce_min_vcpus : 0,
                ce_max_vcpus : lookup(var.ce_max_vcpu, local.environment, 64),
                ce_desired_vcpus : 0,

                jd_memory = 2*(1024-128),
                jd_vcpu = 1,
              },
              { # -------------------------------------------------------------------
                name : "08g",

                # 8g job def -> 8g queue -> 8g compute env
                ce_instance_type = [
                    "m5a.2xlarge",    #  8 cores, 32G     $0.344 / hr, 4 concurrent jobs
                ],

                ce_min_vcpus : 0,
                ce_max_vcpus : lookup(var.ce_max_vcpu, local.environment, 64),
                ce_desired_vcpus : 0,

                jd_memory = 8*(1024-128),
                jd_vcpu = 2,
              },
              { # -------------------------------------------------------------------
                name : "16g",

                # 16g job def -> 16g queue -> 16g compute env
                ce_instance_type = [
                    "r5a.xlarge",    #  4 cores,  32G    $0.226 / hr, 2 concurrent jobs
                ],

                ce_min_vcpus : 0,
                ce_max_vcpus : lookup(var.ce_max_vcpu, local.environment, 64),
                ce_desired_vcpus : 0,

                jd_memory = 16*(1024-128),
                jd_vcpu = 2,
              },
              { # -------------------------------------------------------------------
                name : "64g",

                # 64g job def -> 64g queue -> 64g compute env (r series or something else, enough memory to fit ~2 jobs per ec2)
                ce_instance_type = [
                    "r5a.2xlarge",    #  8 cores, 64G   $0.452 / hr, 1 concurrent job
                ],

                ce_min_vcpus : 0,
                ce_max_vcpus : lookup(var.ce_max_vcpu, local.environment, 64),
                ce_desired_vcpus : 0,

                jd_memory = 64*(1024-128),
                jd_vcpu = 8,
              },
       ]

       # should be kept in sync with the string in deploy_vars.sh
       common_image_spec = "CALCLOUD_%s-CALDP_%s-BASE_%s%s"
       common_image_tag = format(
         local.common_image_spec,
         var.awsysver,
         var.awsdpver,
         var.full_base_image,
         local.environment
       )

       # this ssm param can cause issues if there are spaces
       ecr_address = trim(nonsensitive(data.aws_ssm_parameter.central_ecr.value), " ")
       ecr_predict_lambda_image = "${local.ecr_address}:predict-${local.common_image_tag}"
       ecr_model_training_image = "${local.ecr_address}:training-${local.common_image_tag}"
       ecr_caldp_batch_image = "${local.ecr_address}:batch-${local.common_image_tag}"


       # because we cannot reference ssm params in variables, we have to set the crds bucket here by looking up the desired bucket through a string
       # set in var.crds_bucket. We then use this map to convert that string to the correct ssm param here
       crds_bucket = {
              "test" : nonsensitive(data.aws_ssm_parameter.crds_test.value),
              "ops" : nonsensitive(data.aws_ssm_parameter.crds_ops.value),
       }[lookup(var.crds_bucket, local.environment, "test")]

       # code is cleaner to put this in locals
       crds_context = lookup(var.crds_context, local.environment, var.crds_context["-sb"])

       # environment variables supplied to all lambdas,  see also AWS batch job definition
       common_env_vars = {
           CALCLOUD_ENVIRONMENT = local.environment,
           JOBDEFINITIONS = local.job_definitions,
           JOBQUEUES = local.job_queues,
           BUCKET=aws_s3_bucket.calcloud.id,
       }

       lambda_log_retention_in_days = 365


}
