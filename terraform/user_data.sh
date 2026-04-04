#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nginx git curl awscli

cd /home/ubuntu
if [ ! -d Employee_Asset_Management_Register ]; then
  git clone https://github.com/bigb787/Employee_Asset_Management_Register.git
fi
cd Employee_Asset_Management_Register
git pull origin main || true

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi
mkdir -p data backups

python -c "from app.database import init_db; init_db()"

sudo cp asset-register.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable asset-register
sudo systemctl start asset-register || sudo systemctl restart asset-register

sudo systemctl enable nginx
bash scripts/ensure-nginx-proxy.sh /home/ubuntu/Employee_Asset_Management_Register

(crontab -l 2>/dev/null | grep -v asset-backup.log; echo "0 2 * * * /home/ubuntu/Employee_Asset_Management_Register/scripts/backup.sh >> /var/log/asset-backup.log 2>&1") | crontab -
(crontab -l 2>/dev/null | grep -v asset-health.log; echo "*/5 * * * * /home/ubuntu/Employee_Asset_Management_Register/scripts/healthcheck.sh >> /var/log/asset-health.log 2>&1") | crontab -

echo "user_data complete"
