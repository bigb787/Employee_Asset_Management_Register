#!/usr/bin/env bash
# One script on the EC2 instance: latest code + nginx proxy + app restart.
# Run:  bash scripts/apply-dashboard-on-server.sh
# Then open in browser:  http://<this server's public IP>/
set -euo pipefail
cd /home/ubuntu/Employee_Asset_Management_Register
git pull origin main
sudo bash scripts/ensure-nginx-proxy.sh
echo ""
echo "=== Next step ==="
echo "On your laptop, open:  http://$(curl -sS --connect-timeout 2 --max-time 3 http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo 'YOUR_PUBLIC_IP')/"
echo "(If that metadata curl fails, use the Elastic IP from AWS console.)"
