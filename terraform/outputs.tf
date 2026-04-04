output "ec2_public_ip" {
  description = "Elastic IP attached to the app instance"
  value       = aws_eip.main.public_ip
}

output "s3_bucket" {
  description = "Backup / evidence bucket"
  value       = aws_s3_bucket.backup.bucket
}

output "ssh_command" {
  description = "SSH to the instance (use your private key path)"
  value       = "ssh -i asset-register.pem ubuntu@${aws_eip.main.public_ip}"
}

output "app_url" {
  value = "http://${aws_eip.main.public_ip}"
}

output "api_docs_url" {
  value = "http://${aws_eip.main.public_ip}/docs"
}

output "instance_id" {
  value = aws_instance.app.id
}
