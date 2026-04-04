variable "aws_region" {
  type        = string
  description = "AWS region for all resources."
  default     = "ap-south-1"
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
  type    = string
  default = "asset-register-backup-bigb787"
}

variable "key_pair_name" {
  type    = string
  default = "asset-register-key"
}

variable "public_key_file" {
  type        = string
  description = "Path to SSH public key (e.g. asset-register.pub) relative to this module."
  default     = "asset-register.pub"
}
