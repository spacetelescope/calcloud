variable "image_tag" {
  type = string
  default = "latest"
}

variable "environment" {
  description = "Override to environment value provided by SSM,  takes precedence if specified."
  type = string
  default = null
}

variable region {
  description = "AWS region"
  type = string
  default = "us-east-1"
}

variable awsdpver {
  description = "HST keyword for caldp repo tag version"
  type = string
  default = "undefined"
}

variable awsysver {
  description = "HST keyword for calcloud repo tag version"
  type = string
  default = "undefined"
}

variable csys_ver {
  description = "HST keyword for docker base calibration image tag"
  type = string
  default = "undefined"
}

variable pinned_tf_ver {
  description = "the intended value of the terraform installation in the environment"
  type = string
  default = "0.14.7"
}

variable lt_ebs_type {
  description = "the type of EBS volume used to back the EC2 worker nodes"
  type = map(string)
  default = {
    "-sb" = "gp3"
    "-dev" = "gp2"
    "-test" = "io1"
    "-ops" = "gp2"
  }
}

variable lt_ebs_iops {
  description = "the provisioned iops of the ebs."
  type = map(number)
  # only valid for gp3, io1, io2 volumes
  default = {
    "-sb" = 6000
    "-dev" = 0
    "-test" = 6000
    "-ops" = 0
  }
}

variable lt_ebs_throughput {
  description = "only for gp3 ebs types, the provisioned throughput"
  type = map(number)
  # only valid for gp3 volumes
  default = {
    "-sb" = 500
    "-dev" = 0
    "-test" = 0
    "-ops" = 0
  }
}




variable ce_max_vcpu {
  description = "the max allowed vCPUs in the compute environment"
  type = map(number)
  default = {
    "-sb" = 64
    "-dev" = 128
    "-test" = 128
    "-ops" = 128
  }
}
