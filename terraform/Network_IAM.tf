variable "batchvpc_cidr" {
  type = string
}

variable "batchsn_cidr" {
  type = string
}

resource "aws_vpc" "batchvpc" {
  cidr_block = var.batchvpc_cidr
  enable_dns_hostnames = true
  enable_dns_support = true
}

resource "aws_subnet" "batch_sn" {
    cidr_block = var.batchsn_cidr
    vpc_id = aws_vpc.batchvpc.id
    availability_zone = "us-east-1a"
    map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "batch_gw" {
  vpc_id = aws_vpc.batchvpc.id
}

resource "aws_route_table" "batch_rt" {
  vpc_id = aws_vpc.batchvpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.batch_gw.id
  }
}

resource "aws_route_table_association" "batch_subnet_assoc" {
  subnet_id      = aws_subnet.batch_sn.id
  route_table_id = aws_route_table.batch_rt.id
}

resource "aws_security_group" "batchsg" {
  vpc_id = aws_vpc.batchvpc.id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    cidr_blocks = [
        "0.0.0.0/0",
    ]
    description = "SSH from institute IP only"
    from_port = 22
    ipv6_cidr_blocks = []
    prefix_list_ids = []
    protocol = "tcp"
    security_groups = []
    self = false
    to_port = 22
  }
}

resource "aws_iam_role" "aws_batch_service_role" {
  name = "AWSBatchServiceRole"
  force_detach_policies = true
    assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
        "Service": "batch.amazonaws.com"
        }
    }
    ]
}
  EOF
  description = "Allows Batch to create and manage AWS resources on your behalf."
  tags = {
    "Name" = "AWSBatchServiceRole"
  }
}

resource "aws_iam_role_policy_attachment" "aws_batch_service_role" {
  role       = aws_iam_role.aws_batch_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

resource "aws_iam_role" "ecs_instance_role" {
  name = "HSTDP-BatchInstanceRole"

  assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
          "Service": "ec2.amazonaws.com"
        }
    }
    ]
}
  EOF
  description           = "Role assigned to Batch workers for HST CALCLOUD"
  tags                  = {
    "Name" = "HSTDP-BatchInstanceRole"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_instance_role" {
  role       = aws_iam_role.ecs_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
}

resource "aws_iam_instance_profile" "ecs_instance_role" {
  name = "ecs_instance_role"
  role = aws_iam_role.ecs_instance_role.name
}

resource "aws_iam_role" "batch_job_role" {
    name = "HSTDP-BatchJobRole"
    assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
            "Service": "ecs-tasks.amazonaws.com"
        },
        "Sid": ""
    }
    ]
}
    EOF
    description= "CRDS S3 access and S3 output bucket access."
    tags = {
        "Name" = "HSTDP-BatchJobRole"
    }
}

resource "aws_iam_role" "calcloud_lambda_role" {
    name = "calcloud-hst-trigger-lambda-role"
    description = "Controls resource access for the lambda used to initiate calcloud-hst batch jobs,  nominally Batch and S3 operations."
    assume_role_policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Action": "sts:AssumeRole",
        "Effect": "Allow",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        }
    }
    ]
}
    EOF
    tags = {
        "CALCLOUD" = "calcloud-hst-trigger-lambda-role"
        "Name"     = "calcloud-hst-trigger-lambda-role"
    }
}