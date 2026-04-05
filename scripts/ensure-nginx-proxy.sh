#!/usr/bin/env bash
# Fixes "Welcome to nginx" by replacing the MAIN nginx.conf with a minimal proxy-only config
# (stock Ubuntu loads conf.d before sites-enabled — defaults there win).
#
# Usage on EC2: sudo bash scripts/ensure-nginx-proxy.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/Employee_Asset_Management_Register}"
STANDALONE="$APP_DIR/nginx/standalone-nginx.conf"

if [[ ! -f "$STANDALONE" ]]; then
  echo "ERROR: missing $STANDALONE — git pull and retry."
  exit 1
fi

echo "==> Backup current nginx.conf"
if [[ -f /etc/nginx/nginx.conf ]]; then
  cp -a /etc/nginx/nginx.conf "/etc/nginx/nginx.conf.bak.$(date +%Y%m%d%H%M%S)"
fi

echo "==> Install standalone nginx.conf (no sites-enabled / conf.d includes)"
cp -f "$STANDALONE" /etc/nginx/nginx.conf

echo "==> Clear old vhosts (not used anymore; avoids confusion on next apt change)"
rm -f /etc/nginx/sites-enabled/*
rm -f /etc/nginx/conf.d/*.conf 2>/dev/null || true

echo "==> Test + restart nginx (full restart, not reload)"
nginx -t
systemctl restart nginx

echo "==> Restart FastAPI upstream"
systemctl restart asset-register || true
sleep 2
systemctl is-active --quiet asset-register && echo "asset-register: active" || echo "WARNING: asset-register failed — journalctl -u asset-register -n 80 --no-pager"

echo "==> Response check (should contain Employee Asset or html from FastAPI, NOT 'Welcome to nginx')"
BODY=$(curl -sS http://127.0.0.1/ | head -c 400 | tr '\n' ' ')
echo "$BODY"
echo ""
if echo "$BODY" | grep -qi 'welcome to nginx'; then
  echo "STILL seeing welcome text — check: sudo nginx -T | head -80"
  exit 1
fi

curl -s -o /dev/null -w "HTTP %{http_code} :8000 direct\n" http://127.0.0.1:8000/ || true
curl -s -o /dev/null -w "HTTP %{http_code} :80 nginx\n" http://127.0.0.1/ || true
echo "Done."
