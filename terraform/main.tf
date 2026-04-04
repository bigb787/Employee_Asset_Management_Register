provider "aws" {
  region = var.aws_region
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ssm_parameter" "ubuntu_22_ami" {
  name = "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"
}

resource "aws_key_pair" "main" {
  key_name   = var.key_pair_name
  public_key = file("${path.module}/${var.public_key_file}")
}

resource "aws_security_group" "app" {
  # name_prefix avoids InvalidGroup.Duplicate when an old SG with a fixed name
  # remains in the VPC but is not in Terraform state (partial apply / new state).
  name_prefix = "${var.app_name}-sg-"
  description = "SSH, HTTP, HTTPS for ${var.app_name}"
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

resource "aws_iam_role" "ec2_s3" {
  name = "${var.app_name}-ec2-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.app_name}-ec2-s3-role"
  }
}

resource "aws_iam_role_policy" "ec2_s3_bucket" {
  name = "${var.app_name}-s3-bucket-access"
  role = aws_iam_role.ec2_s3.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListBucket"
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = [
          aws_s3_bucket.backup.arn
        ]
      },
      {
        Sid    = "ObjectRW"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.backup.arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.app_name}-ec2-profile"
  role = aws_iam_role.ec2_s3.name
}

resource "aws_instance" "app" {
  ami                    = nonsensitive(data.aws_ssm_parameter.ubuntu_22_ami.value)
  instance_type          = var.instance_type
  key_name               = aws_key_pair.main.key_name
  vpc_security_group_ids = [aws_security_group.app.id]
  subnet_id              = data.aws_subnets.default.ids[0]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  user_data = file("${path.module}/user_data.sh")

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name = var.app_name
  }

  depends_on = [
    aws_iam_instance_profile.ec2
  ]
}

resource "aws_eip" "main" {
  domain   = "vpc"
  instance = aws_instance.app.id

  tags = {
    Name = "${var.app_name}-eip"
  }
}

resource "aws_s3_bucket" "backup" {
  bucket        = var.s3_bucket_name
  force_destroy = false

  # Avoid indefinite "Still creating..." when HTTPS to S3 never completes (VPN/proxy/firewall).
  timeouts {
    create = "10m"
    delete = "10m"
  }

  tags = {
    Name = var.s3_bucket_name
  }
}

resource "aws_s3_bucket_public_access_block" "backup" {
  bucket = aws_s3_bucket.backup.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "backup" {
  bucket = aws_s3_bucket.backup.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = false
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id

  rule {
    id     = "expire-backups-after-30-days"
    status = "Enabled"

    filter {
      prefix = "backups/"
    }

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }

  depends_on = [aws_s3_bucket_versioning.backup]
}
