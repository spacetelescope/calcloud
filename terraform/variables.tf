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
