output "ec2_public_ip" {
  value = aws_eip.main.public_ip
}

output "s3_bucket" {
  value = aws_s3_bucket.backup.bucket
}

output "ssh_command" {
  value = "ssh -i asset-register ubuntu@${aws_eip.main.public_ip}"
}

output "app_url" {
  value = "http://${aws_eip.main.public_ip}"
}

output "api_docs_url" {
  value = "http://${aws_eip.main.public_ip}/docs"
}
