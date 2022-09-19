resource aws_codebuild_project ami_rotation {
    name         = "calcloud-ami-rotation${local.environment}"
    service_role = data.aws_ssm_parameter.codebuild_ami_rotate_arn.value

    artifacts {
        type = "NO_ARTIFACTS"
    }

    cache {
        type = "NO_CACHE"
    }

    environment {
        compute_type    = "BUILD_GENERAL1_SMALL"
        image           = "${var.ami_rotation_base_image}"
        type            = "LINUX_CONTAINER"
        privileged_mode = true
        image_pull_credentials_type = "SERVICE_ROLE"

        environment_variable {
            name  = "ADMIN_ARN"
            value = "${data.aws_ssm_parameter.admin_arn.value}"
        }

        environment_variable {
            name  = "AWS_DEFAULT_REGION"
            value = "${var.region}"
        }

        environment_variable {
            name  = "aws_env"
            value = "${local.pre_environment}"
        }
	
       environment_variable {
            name  = "CALCLOUD_BUILD_DIR"
            value = "/opt/calcloud/ami_rotate/calcloud"
        }
    
    }

    logs_config {
        cloudwatch_logs {
            group_name  = "/aws/codebuild"
            stream_name = "calcloud-ami-rotation"
        }
    }

    source {
        type            = "NO_SOURCE"
        buildspec       = file("buildspecs/ami-rotation.spec")
    }
}
