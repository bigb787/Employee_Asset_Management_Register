#!/bin/bash
set -e
ENV_FILE="/home/ubuntu/Employee_Asset_Management_Register/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ENV_FILE"
  set +a
fi
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H-%M)
DB=/home/ubuntu/Employee_Asset_Management_Register/data/assets.db
BUCKET="${S3_BUCKET_NAME:-asset-register-backup-bigb787}"
LOG=/var/log/asset-backup.log
echo "[$(date)] Starting backup" >> "$LOG"
aws s3 cp "$DB" "s3://$BUCKET/backups/assets-$DATE-$TIME.db"
echo "[$(date)] Backup done: assets-$DATE-$TIME.db" >> "$LOG"
aws s3 ls "s3://$BUCKET/backups/" | while read -r line; do
  d=$(echo "$line" | awk '{print $1}')
  ts=$(date -d "$d" +%s 2>/dev/null || echo 0)
  old=$(date -d "30 days ago" +%s)
  if [[ $ts -lt $old ]]; then
    f=$(echo "$line" | awk '{print $4}')
    if [[ -n "$f" ]]; then
      aws s3 rm "s3://$BUCKET/backups/$f"
      echo "[$(date)] Deleted old: $f" >> "$LOG"
    fi
  fi
done
