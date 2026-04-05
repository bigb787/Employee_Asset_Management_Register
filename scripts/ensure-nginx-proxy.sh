#!/usr/bin/env bash
# Run on the EC2 instance if you only see "Welcome to nginx" instead of the app.
# Usage: sudo bash scripts/ensure-nginx-proxy.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/Employee_Asset_Management_Register}"

echo "==> Disabling stock nginx default sites (they serve the welcome page)"
rm -f /etc/nginx/sites-enabled/default
rm -f /etc/nginx/conf.d/default.conf 2>/dev/null || true

echo "==> Enabling asset-register site"
install -d /etc/nginx/sites-available
cp -f "$APP_DIR/nginx.conf" /etc/nginx/sites-available/asset-register
ln -sf /etc/nginx/sites-available/asset-register /etc/nginx/sites-enabled/asset-register

echo "==> Testing nginx config"
nginx -t

echo "==> Reloading nginx"
systemctl reload nginx

echo "==> Restarting FastAPI (so upstream :8000 is up)"
systemctl restart asset-register || true
sleep 2
systemctl is-active --quiet asset-register && echo "asset-register: active" || echo "WARNING: asset-register is not active — run: journalctl -u asset-register -n 50 --no-pager"

echo "==> Local checks"
curl -s -o /dev/null -w "HTTP %{http_code} from app direct\n" http://127.0.0.1:8000/ || true
curl -s -o /dev/null -w "HTTP %{http_code} via nginx\n" http://127.0.0.1/ || true

echo "Done. Open http://<your-server-ip>/ in a browser."
