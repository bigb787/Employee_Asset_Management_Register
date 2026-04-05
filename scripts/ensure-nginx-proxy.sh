#!/usr/bin/env bash
# Run on the EC2 instance if you only see "Welcome to nginx" instead of the app.
# Usage: sudo bash scripts/ensure-nginx-proxy.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/home/ubuntu/Employee_Asset_Management_Register}"

echo "==> Stop nginx briefly (clean listen on :80)"
systemctl stop nginx || true

echo "==> Remove stock configs that serve the welcome page on port 80"
# conf.d is often included BEFORE sites-enabled — default.conf wins first.
rm -f /etc/nginx/conf.d/default.conf
rm -f /etc/nginx/conf.d/default
shopt -s nullglob
for f in /etc/nginx/conf.d/*.conf; do
  # Drop any leftover default-style server on 80 (dedicated app VM only)
  if grep -qE '^\s*listen\s+(\[::\]:)?80' "$f" 2>/dev/null; then
    echo "    removing $f (listens on 80)"
    rm -f "$f"
  fi
done
shopt -u nullglob

echo "==> sites-enabled: only asset-register (remove default symlink, etc.)"
rm -f /etc/nginx/sites-enabled/default
install -d /etc/nginx/sites-available /etc/nginx/sites-enabled
for f in /etc/nginx/sites-enabled/*; do
  [ -e "$f" ] || continue
  base=$(basename "$f")
  if [ "$base" != "asset-register" ]; then
    echo "    removing sites-enabled/$base"
    rm -f "$f"
  fi
done

echo "==> Install our vhost"
cp -f "$APP_DIR/nginx.conf" /etc/nginx/sites-available/asset-register
ln -sf /etc/nginx/sites-available/asset-register /etc/nginx/sites-enabled/asset-register

echo "==> Test + start nginx"
nginx -t
systemctl start nginx
systemctl enable nginx

echo "==> Restart FastAPI (upstream :8000)"
systemctl restart asset-register || true
sleep 2
systemctl is-active --quiet asset-register && echo "asset-register: active" || echo "WARNING: asset-register is not active — run: journalctl -u asset-register -n 80 --no-pager"

echo "==> Which server answers :80 (first 500 chars of response body)"
curl -s http://127.0.0.1/ | head -c 500 | tr '\n' ' '
echo ""
echo "==> HTTP codes"
curl -s -o /dev/null -w "direct app :8000  -> %{http_code}\n" http://127.0.0.1:8000/ || true
curl -s -o /dev/null -w "via nginx :80     -> %{http_code}\n" http://127.0.0.1/ || true

echo "Done. If body still mentions nginx welcome, paste: sudo nginx -T"
