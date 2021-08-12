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
  default = "0.15.4"
}

# valid combos
# type: iops, throughput
# gp2: null, null
# gp3: null, number
# io1: number, null
# io2: number, null
variable lt_ebs_type {
  description = "the type of EBS volume used to back the EC2 worker nodes"
  type = map(string)
  default = {
    "-sb" = "gp2"
    "-dev" = "gp2"
    "-test" = "gp3"
    "-ops" = "gp3"
  }
}

variable lt_ebs_iops {
  description = "the provisioned iops of the ebs."
  type = map(number)
  # only valid for gp3, io1, io2 volumes
  # gp2 does not like null; it makes the compute env turn to invalid
  default = {
    "-sb" = 0
    "-dev" = 0
    "-test" = 3000
    "-ops" = 3000
  }
}

variable lt_ebs_throughput {
  description = "only for gp3 ebs types, the provisioned throughput"
  type = map(number)
  # only valid for gp3 volumes
  # io1 seems to require saying something that's not 0, but null works
  default = {
    "-sb" = null
    "-dev" = null
    "-test" = 250
    "-ops" = 250
  }
}

variable ce_max_vcpu {
  description = "the max allowed vCPUs in the compute environment"
  type = map(number)
  default = {
    "-sb" = 64
    "-dev" = 128
    "-test" = 1024
    "-ops" = 2048
  }
}

variable crds_context {
  description = "the crds context to be the default for the environment"
  type = map(string)
  default = {
    "-sb" = "hst_0866.pmap"
    "-dev" = "hst_0866.pmap"
    "-test" = "hst_0939.pmap"
    "-ops" = "hst_0939.pmap"
  }
}

variable crds_bucket {
  type = map(string)
  default = {
    "-sb" = "test"
    "-dev" = "test"
    "-test" = "ops"
    "-ops" = "ops"
  }
}
