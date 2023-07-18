resource aws_codebuild_project ami_rotation {
    name         = "calcloud-ami-rotation${local.environment}"
    service_role = "arn:aws:iam::${var.account_id}:role/service-role/${data.aws_ssm_parameter.codebuild_role_name.value}"

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
            name  = "TF_VAR_account_id"
            value = "${var.account_id}"
        }

        environment_variable {
            name  = "AWS_DEFAULT_REGION"
            value = "${var.region}"
        }

        environment_variable {
            name  = "aws_env"
            value = "${local.pre_environment}"
        }
	
        # Uncomment to use the CALCLOUD version built into the codebuild image 
        # instead of pulling latest version from github
        #environment_variable {
        #     name  = "CALCLOUD_BUILD_DIR"
        #     value = "/opt/calcloud/ami_rotate/calcloud"
        #}
    
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

resource "aws_cloudwatch_event_rule" "ami-rotate-scheduler-codebuild" {
  name                = "ami-rotate-scheduler-codebuild${local.environment}"
  description         = "scheduler for ami rotation with code build"
  schedule_expression = "cron(0 9 ? * TUE,FRI *)"
}

resource "aws_cloudwatch_event_target" "ami-rotate-scheduler-codebuild" {
  rule      = aws_cloudwatch_event_rule.ami-rotate-scheduler-codebuild.name
  target_id = "codebuild"
  arn       = aws_codebuild_project.ami_rotation.arn
  role_arn  = "arn:aws:iam::${var.account_id}:role/service-role/${data.aws_ssm_parameter.codebuild_role_name.value}" 
}
