variable "aws_region" {
  type        = string
  description = "AWS region for all resources"
  default     = "us-east-1"
}

variable "aws_profile" {
  type        = string
  description = "Named profile from ~/.aws/credentials; leave empty to use the default credential chain or AWS_PROFILE env."
  default     = ""
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "app_name" {
  type    = string
  default = "employee-asset-register"
}

variable "s3_bucket_name" {
  type        = string
  description = "Globally unique S3 bucket name"
  default     = "asset-register-backup-bigb787"
}

variable "key_pair_name" {
  type    = string
  default = "asset-register-key"
}

variable "public_key_path" {
  type        = string
  description = "Path to SSH public key file (project root), e.g. ../asset-register.pub relative to terraform/"
  default     = "../asset-register.pub"
}

variable "volume_size_gb" {
  type    = number
  default = 20
}
