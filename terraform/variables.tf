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
    "-sb" = "gp2"
    "-dev" = "gp2"
    "-test" = "gp3"
    "-ops" = "gp3"
  }
}
