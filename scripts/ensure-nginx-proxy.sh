#!/usr/bin/env bash
# Force this app as the only vhost on :80 (fixes stock "Welcome to nginx!" page).
set -euo pipefail
shopt -s nullglob

REPO="${1:-/home/ubuntu/Employee_Asset_Management_Register}"
if [[ ! -f "$REPO/nginx.conf" ]]; then
  echo "Missing $REPO/nginx.conf" >&2
  exit 1
fi

echo "=== before: sites-enabled ==="
ls -la /etc/nginx/sites-enabled/ 2>/dev/null || true
echo "=== before: conf.d ==="
ls -la /etc/nginx/conf.d/ 2>/dev/null || true

sudo rm -f /etc/nginx/conf.d/default.conf

for f in /etc/nginx/sites-enabled/*; do
  sudo rm -f "$f"
done

sudo cp "$REPO/nginx.conf" /etc/nginx/sites-available/asset-register
sudo ln -sf /etc/nginx/sites-available/asset-register /etc/nginx/sites-enabled/00-asset-register

sudo nginx -t
sudo systemctl reload nginx 2>/dev/null || sudo systemctl restart nginx

echo "=== after: sites-enabled ==="
ls -la /etc/nginx/sites-enabled/

echo "=== local checks ==="
echo -n "port 80: "
curl -sS -o /tmp/ng80.txt -w "%{http_code}\n" http://127.0.0.1/ || echo "curl failed"
head -c 120 /tmp/ng80.txt 2>/dev/null | tr '\n' ' '
echo
echo -n "api/stats: "
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/api/stats || echo "curl failed (is asset-register running?)"
