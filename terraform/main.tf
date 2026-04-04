provider "aws" {
  region = var.aws_region
  # Credentials: default chain ([default] profile, env vars, or AWS_PROFILE).
  # Set `aws_profile` in tfvars only when using the optional `profile` attribute below.
  profile = var.aws_profile != "" ? var.aws_profile : null
}

data "aws_caller_identity" "current" {}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_key_pair" "app" {
  key_name   = var.key_pair_name
  public_key = file(var.public_key_path)
}

resource "aws_security_group" "app" {
  name        = "${var.app_name}-sg"
  description = "SSH, HTTP, HTTPS for asset register"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.app_name}-sg"
  }
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2_s3" {
  name               = "${var.app_name}-ec2-s3"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json

  tags = {
    Name = "${var.app_name}-ec2-s3"
  }
}

data "aws_iam_policy_document" "s3_backup" {
  statement {
    sid    = "ListBucket"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
    ]
    resources = [
      aws_s3_bucket.backup.arn,
    ]
  }

  statement {
    sid    = "ObjectRW"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]
    resources = [
      "${aws_s3_bucket.backup.arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "ec2_s3" {
  name   = "${var.app_name}-s3-access"
  role   = aws_iam_role.ec2_s3.id
  policy = data.aws_iam_policy_document.s3_backup.json
}

resource "aws_iam_instance_profile" "app" {
  name = "${var.app_name}-profile"
  role = aws_iam_role.ec2_s3.name
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.app.key_name
  vpc_security_group_ids = [aws_security_group.app.id]
  subnet_id              = data.aws_subnets.default.ids[0]
  iam_instance_profile   = aws_iam_instance_profile.app.name

  user_data = file("${path.module}/user_data.sh")

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.volume_size_gb
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name = var.app_name
  }
}

resource "aws_eip" "main" {
  domain = "vpc"
  tags = {
    Name = "${var.app_name}-eip"
  }
}

resource "aws_eip_association" "main" {
  instance_id   = aws_instance.app.id
  allocation_id = aws_eip.main.id
}

resource "aws_s3_bucket" "backup" {
  bucket        = var.s3_bucket_name
  force_destroy = false

  tags = {
    Name = var.s3_bucket_name
  }

  # Avoid indefinite wait if the API stalls; surface a clear timeout error instead.
  timeouts {
    create = "15m"
    delete = "15m"
  }
}

resource "aws_s3_bucket_public_access_block" "backup" {
  bucket = aws_s3_bucket.backup.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
