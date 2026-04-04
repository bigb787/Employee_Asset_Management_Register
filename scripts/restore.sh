#!/bin/bash
set -e
ENV_FILE="/home/ubuntu/Employee_Asset_Management_Register/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi
BUCKET="${S3_BUCKET_NAME:-asset-register-backup-bigb787}"
echo "Available backups:"
aws s3 ls "s3://$BUCKET/backups/" | awk '{print NR". "$4}'
read -p "Enter filename to restore: " FNAME
DB=/home/ubuntu/Employee_Asset_Management_Register/data/assets.db
cp "$DB" "${DB}.bak-$(date +%Y%m%d%H%M%S)"
echo "Current DB backed up locally"
aws s3 cp "s3://$BUCKET/backups/$FNAME" "$DB"
sudo systemctl restart asset-register
echo "Restore complete. App restarted."
