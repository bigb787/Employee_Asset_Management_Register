#!/bin/bash
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y software-properties-common
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update -y
apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip nginx git curl build-essential

APP_DIR="/home/ubuntu/Employee_Asset_Management_Register"
install -d -o ubuntu -g ubuntu /home/ubuntu

if [ ! -d "$APP_DIR/.git" ]; then
  sudo -u ubuntu git clone https://github.com/bigb787/Employee_Asset_Management_Register.git "$APP_DIR"
else
  sudo -u ubuntu git -C "$APP_DIR" pull --ff-only || true
fi

sudo -u ubuntu python3.11 -m venv "$APP_DIR/venv"
sudo -u ubuntu bash -lc "cd $APP_DIR && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

if [ -f "$APP_DIR/.env" ]; then
  :
else
  sudo -u ubuntu cp "$APP_DIR/.env.example" "$APP_DIR/.env"
fi

sudo -u ubuntu mkdir -p "$APP_DIR/data" "$APP_DIR/backups"

sudo -u ubuntu bash -lc "cd $APP_DIR && source venv/bin/activate && python3 -c 'from app.database import init_db; init_db()'"

cp "$APP_DIR/asset-register.service" /etc/systemd/system/asset-register.service
systemctl daemon-reload
systemctl enable asset-register
systemctl restart asset-register || systemctl start asset-register

cp "$APP_DIR/nginx.conf" /etc/nginx/sites-available/asset-register
ln -sf /etc/nginx/sites-available/asset-register /etc/nginx/sites-enabled/asset-register
rm -f /etc/nginx/sites-enabled/default
systemctl enable nginx
systemctl restart nginx

(sudo -u ubuntu crontab -l 2>/dev/null | grep -v "scripts/backup.sh" || true; echo "0 2 * * * /home/ubuntu/Employee_Asset_Management_Register/scripts/backup.sh >> /var/log/asset-backup.log 2>&1") | sudo -u ubuntu crontab -
(sudo -u ubuntu crontab -l 2>/dev/null | grep -v "scripts/healthcheck.sh" || true; echo "*/5 * * * * /home/ubuntu/Employee_Asset_Management_Register/scripts/healthcheck.sh >> /var/log/asset-health.log 2>&1") | sudo -u ubuntu crontab -
